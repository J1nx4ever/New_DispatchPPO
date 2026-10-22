from __future__ import annotations

import numpy as np
import pytest

from python.window_projection import project_fifo_only, decode_fifo


def obs(t=0.0, window=0, rate=2500.0, batches=()):
    a = np.zeros(1519, dtype=np.float32)
    a[0] = np.float32(t/28800.0)
    a[1] = np.float32(max(0.0, 28800.0-t)/28800.0)
    a[2] = np.float32(window/4.0)
    a[3] = np.float32(max(0.0, min(28800.0, (window+1)*7200.0)-t)/7200.0)
    a[17] = float(window == 4)
    a[1304] = np.float32(rate/2500.0)
    a[1300] = np.float32(sum(q for q,_ in batches)/500.0)
    for i,(q,g) in enumerate(batches):
        k=1391+3*i
        a[k] = 1
        a[k+1] = np.float32(q/500.0)
        a[k+2] = np.float32(g)
    return a


def test_current_and_next_and_mass_metal_conservation():
    # 2500 t/h = 0.6944 t/s. At t=7100, only 69.444 t can be
    # processed before window boundary; the remaining 130.556 t -> next.
    p=project_fifo_only(obs(7100,0,batches=[(100,.2),(100,.4)]))
    a=100*2500/3600
    assert p.produced_tons_by_window[0] == pytest.approx(a,abs=0.0005)
    assert p.produced_tons_by_window[1] == pytest.approx(200-a,abs=0.0005)
    assert p.produced_metal_by_window[0] == pytest.approx(a*.2,abs=0.0005)
    assert sum(p.produced_tons_by_window) == pytest.approx(200,abs=0.0005)
    assert sum(p.produced_metal_by_window) == pytest.approx(60,abs=0.0005)
    assert p.features[2] == 1 and p.features[5] == 1


def test_empty_fifo_is_valid_zero_contribution():
    z=project_fifo_only(obs(100,0)).features
    assert z.tolist() == [0,0,1,0,0,1]


def test_final_window_next_invalid():
    z=project_fifo_only(obs(24000,3,batches=[(250,.26)])).features
    assert z[2] == 1
    assert list(z[3:]) == [0,0,0]


def test_terminal_both_invalid():
    z=project_fifo_only(obs(28800,4,batches=[(100,.3)])).features
    assert z.tolist() == [0]*6


def test_strict_fifo_mass_audit():
    x=obs(100,0,batches=[(150,.3)])
    x[1300]=0.0
    with pytest.raises(ValueError,match="FIFO mass"):
        decode_fifo(x)


def test_fifo_no_hole():
    x=obs(0,0,batches=[(100,.2)])
    x[1391]=0; x[1392]=0; x[1393]=0
    x[1394]=1; x[1395]=.2; x[1396]=.2
    with pytest.raises(ValueError,match="after empty"):
        decode_fifo(x,check_buffer=False)


def test_window_boundary_exact():
    p=project_fifo_only(obs(7200,1,batches=[(500,.3)]))
    assert p.produced_tons_by_window[0] == 0
    assert p.produced_tons_by_window[1] == pytest.approx(500)


def test_wrapper_appends_six_fields_and_preserves_raw():
    from python.dispatch_bridge import DispatchCallbackBridge
    from python.dispatch_env import DispatchEnv
    from python.observation_contract import AGENT_OBSERVATION_SIZE
    from python.observation_projection_wrapper import FIFOObservationWrapper

    raw=obs(7100,0,batches=[(100,.2),(100,.4)])
    env=FIFOObservationWrapper(DispatchEnv(DispatchCallbackBridge()))
    assert env.observation_space.shape==(AGENT_OBSERVATION_SIZE,)
    assert env.observation_space.shape==(1525,)
    out=env.observation(raw)
    assert out.shape==(1525,) and out.dtype==np.float32
    np.testing.assert_array_equal(out[:1519],raw)
    expected=project_fifo_only(raw).features
    np.testing.assert_allclose(out[1519:],expected,rtol=0,atol=0)
    assert env.observation_space.contains(out)


def test_wrapper_rejects_wrong_dimension():
    from python.dispatch_bridge import DispatchCallbackBridge
    from python.dispatch_env import DispatchEnv
    from python.observation_projection_wrapper import FIFOObservationWrapper

    env=FIFOObservationWrapper(DispatchEnv(DispatchCallbackBridge()))
    with pytest.raises(ValueError,match="expected raw observation"):
        env.observation(np.zeros(1525,dtype=np.float32))


@pytest.mark.parametrize('t,window', [(7200,1),(14400,2),(21600,3)])
@pytest.mark.parametrize('offset', [-1e-4, 0, 1e-4])
def test_clock_at_every_boundary(t,window,offset):
    actual = t+offset
    index = window if offset >= 0 else window-1
    p = project_fifo_only(obs(actual,index,batches=[(200,.3)]))
    assert p.current_window == index
    assert abs(p.observation_time_seconds-actual) <= p.observation_time_error_seconds + 1e-10
    assert p.features[2] == 1


def test_near_shift_end_not_misread_as_terminal():
    raw = obs(28800-1e-5,3,batches=[(100,.3)])
    assert raw[0] == 1  # float32 elapsed has lost the remaining microseconds.
    p = project_fifo_only(raw)
    assert p.features[2] == 1 and p.features[5] == 0
    assert p.produced_tons_by_window[3] == pytest.approx(1e-5*2500/3600, abs=1e-11)
    assert p.remaining_after_shift_tons > 99.99


@pytest.mark.parametrize('index,value', [(0,-.1),(0,1.01),(1,0),(1,1.01),(2,.1),
                                         (2,1.25),(3,-.1),(3,0),(3,1.01),(17,.5)])
def test_bad_clock_values_fail_explicitly(index,value):
    raw = obs(100,0)
    raw[index] = value
    with pytest.raises(ValueError): project_fifo_only(raw)


@pytest.mark.parametrize('t,window', [(15000,0),(100,4),(100,1),(28800,3)])
def test_stale_or_inconsistent_window_rejected(t,window):
    with pytest.raises(ValueError): project_fifo_only(obs(t,window,batches=[(100,.3)]))


def test_mutually_inconsistent_remaining_clocks_rejected():
    raw = obs(100,0)
    raw[1] = .5
    with pytest.raises(ValueError,match='clocks disagree'): project_fifo_only(raw)


@pytest.mark.parametrize('index,value', [(1391,.5),(1392,-.1),(1392,0),
                                         (1393,-.01),(1393,1.01),(1304,0),(1304,-1),
                                         (1300,-1),(1394,0.1)])
def test_bad_fifo_or_rate_rejected(index,value):
    raw = obs(100,0,batches=[(100,.3)])
    raw[index] = value
    with pytest.raises(ValueError): project_fifo_only(raw)


@pytest.mark.parametrize('value', [float('nan'),float('inf'),-float('inf'),1e100])
def test_nonfinite_or_overflow_rejected(value):
    raw = obs(100,0).astype(np.float64)
    raw[100] = value
    with pytest.raises(ValueError): project_fifo_only(raw)


def test_fifo_sixteen_slots_and_unreported_mass_fail():
    raw = obs(0,0,batches=[(10,.1+.02*i) for i in range(16)])
    p = project_fifo_only(raw)
    assert p.initial_fifo_tons == pytest.approx(160,abs=1e-5)
    assert len(decode_fifo(raw)) == 16
    raw[1300] += 10/500  # hidden 17th batch would break the public mass balance.
    with pytest.raises(ValueError,match='FIFO mass'): project_fifo_only(raw)


def test_head_is_remaining_material_and_fifo_order_controls_metal():
    # A partially processed head already has just 25t left; never subtract age again.
    raw = obs(7190,0,batches=[(25,.1),(100,.5)])
    p = project_fifo_only(raw)
    assert p.initial_fifo_tons == pytest.approx(125,abs=1e-5)
    q = 10*2500/3600
    assert p.produced_metal_by_window[0] == pytest.approx(q*.1,abs=1e-6)
    swapped = project_fifo_only(obs(7190,0,batches=[(100,.5),(25,.1)]))
    assert swapped.produced_tons_by_window == pytest.approx(p.produced_tons_by_window)
    assert swapped.produced_metal_by_window[0] == pytest.approx(q*.5,abs=1e-6)


def test_does_not_add_already_produced_reserved_or_carried_material():
    raw = obs(100,0,batches=[(100,.3)])
    base = project_fifo_only(raw)
    changed = raw.copy()
    changed[4:6] = [3,.9]       # window already produced (deliberately unphysical magnitude).
    changed[1301] = 100/500    # reservation is not another FIFO batch.
    changed[46:50] = [.5,.5,1,.4]
    np.testing.assert_array_equal(project_fifo_only(changed).features,base.features)
    np.testing.assert_array_equal(raw,obs(100,0,batches=[(100,.3)]))


def test_final_shift_residual_mass_and_metal_conserved():
    p = project_fifo_only(obs(28700,3,batches=[(100,.2),(100,.4)]))
    assert sum(p.produced_tons_by_window)+p.remaining_after_shift_tons == pytest.approx(p.initial_fifo_tons)
    assert sum(p.produced_metal_by_window)+p.remaining_after_shift_metal_tons == pytest.approx(p.initial_fifo_metal_tons)
    assert p.remaining_after_shift_tons > 100
    assert p.remaining_after_shift_metal_tons > 40
    assert p.features[5] == 0


def test_feature_normalization_is_fixed_and_not_clipped():
    # General arithmetic stress case, outside the current 500t physical buffer.
    p = project_fifo_only(obs(0,0,rate=5000,batches=[(6000,1)]))
    assert p.features.tolist() == pytest.approx([1.2,1.2,1,0,0,1])


def test_all_used_schema_fields_are_checked():
    from python.observation_contract import FIELD_NAMES
    from python.window_projection import assert_schema_fields
    assert_schema_fields(FIELD_NAMES)
    names = list(FIELD_NAMES)
    names[1408] = 'wrong.middle.fifo.grade'
    with pytest.raises(ValueError,match='index 1408'): assert_schema_fields(names)


def test_random_states_match_independent_batch_interval_reference():
    # Independent reference: intersect each batch's processing interval with each
    # fixed window, instead of stepping the production loop by window and batch.
    rng = np.random.default_rng(20261022)
    for _ in range(300):
        t = rng.uniform(0,28800)
        window = int(t//7200)
        count = int(rng.integers(0,17))
        tons = rng.uniform(.01,25,count)
        grades = rng.uniform(0,1,count)
        raw = obs(t,window,rate=float(rng.uniform(100,5000)),batches=list(zip(tons,grades)))
        original = raw.copy()
        p = project_fifo_only(raw)
        rate = float(raw[1304])*2500/3600
        cursor = t
        expected_q = np.zeros(4)
        expected_m = np.zeros(4)
        for batch in decode_fifo(raw):
            end = cursor+batch.remaining_tons/rate
            for w in range(4):
                overlap = max(0,min(end,(w+1)*7200)-max(cursor,w*7200))
                expected_q[w] += overlap*rate
                expected_m[w] += overlap*rate*batch.grade_fraction
            cursor = end
        atol = 2*rate*p.observation_time_error_seconds+1e-7
        np.testing.assert_allclose(p.produced_tons_by_window,expected_q,rtol=0,atol=atol)
        np.testing.assert_allclose(p.produced_metal_by_window,expected_m,rtol=0,atol=atol)
        assert sum(p.produced_tons_by_window)+p.remaining_after_shift_tons == pytest.approx(p.initial_fifo_tons,abs=1e-7)
        assert sum(p.produced_metal_by_window)+p.remaining_after_shift_metal_tons == pytest.approx(p.initial_fifo_metal_tons,abs=1e-7)
        np.testing.assert_array_equal(raw,original)


def test_recorded_parameter_sources_and_reward_v1_are_consistent():
    import hashlib
    from pathlib import Path
    from python.alp_audit import validate_alp_contract
    from python.window_projection import PARAMETERS
    root = Path(__file__).resolve().parents[1]
    source = PARAMETERS['source']
    assert hashlib.sha256((root/source['alp_path']).read_bytes()).hexdigest() == source['alp_sha256']
    assert hashlib.sha256((root/source['schema_path']).read_bytes()).hexdigest() == source['schema_sha256']
    assert validate_alp_contract(root/source['alp_path'])['reward_contract'] == source['reward_contract_id']
    assert source['fitting_data'] is None


def test_wire_roundtrip_stays_1519_and_projection_stays_separate():
    from python.dispatch_bridge import observation_array
    from python.generated import dispatch_pb2 as pb
    raw = obs(7190,0,batches=[(25,.1),(100,.5)])
    raw[19] = raw[27] = 1
    request = pb.DispatchRequest(kind=pb.DECISION,truck_id=0,
        obs=pb.Observation(schema_id='dispatch.physical.v3',values=raw))
    received = pb.DispatchRequest.FromString(request.SerializeToString())
    decoded = observation_array(received)
    result = project_fifo_only(decoded)
    assert len(received.obs.values) == 1519 and result.features.shape == (6,)
    np.testing.assert_array_equal(decoded,raw)


def test_terminal_pending_material_is_not_discarded_by_diagnostics():
    p = project_fifo_only(obs(28800,4,batches=[(100,.2),(100,.4)]))
    assert sum(p.produced_tons_by_window) == sum(p.produced_metal_by_window) == 0
    assert p.remaining_after_shift_tons == pytest.approx(200,abs=1e-5)
    assert p.remaining_after_shift_metal_tons == pytest.approx(60,abs=1e-5)
    assert list(p.features) == [0]*6
