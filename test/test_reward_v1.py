"""Frozen V1.0 behavior and fail-closed source provenance regressions."""
import xml.etree.ElementTree as ET

import pytest

from python.alp_audit import load_alp, validate_alp_contract, validate_alp_sources
from python.reward_config import RewardConfiguration, configuration_from_components, configuration_to_components
from python.reward_contract import (
    ADDITIVE_COMPONENTS, FROZEN_REWARD_PARAMETERS, REWARD_CONTRACT_ID,
    validate_reward_accounting, validate_window_summary, window_summary_to_dict,
)
from python.dispatch_bridge import DispatchCallbackBridge, ProtocolError
from python.generated import dispatch_pb2 as pb
from test_contracts import request, windows, ROOT
from test_alp_experiment import model, write_model


@pytest.mark.parametrize('kwargs', [
    {'grade_action_enabled': True}, {'waste_shortfall_weight': 0},
    {'waste_shortfall_weight': 2.5}, {'waste_target_tons': 0},
    {'waste_target_tons': 2000},
])
def test_nonfrozen_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError, match='frozen'):
        RewardConfiguration(**kwargs)


@pytest.mark.parametrize('key', list(FROZEN_REWARD_PARAMETERS))
def test_every_reward_constant_is_explicit_and_frozen(key):
    components = configuration_to_components(RewardConfiguration())
    del components['config.' + key]
    with pytest.raises(ValueError, match='configuration missing'):
        configuration_from_components(components)
    components = configuration_to_components(RewardConfiguration())
    components['config.' + key] += 0.5
    with pytest.raises(ValueError, match='runtime parameter'):
        configuration_from_components(components)


@pytest.mark.parametrize('field', ['grade_action', 'grade_shift'])
@pytest.mark.parametrize('leak', [-1e-12, 1e-12, 6.0])
def test_disabled_rewards_must_be_exact_zero(field, leak):
    r = request(pb.EPISODE_END, 1, 0, 28800)
    r.reward_components[field] = leak
    r.transition_reward = sum(r.reward_components[k] for k in ADDITIVE_COMPONENTS)
    with pytest.raises(ProtocolError, match='exactly zero'):
        DispatchCallbackBridge._validate_request(r)


@pytest.mark.parametrize('ore', [0, 8000, 16000, 20000])
@pytest.mark.parametrize('waste', [0, 2000, 4000, 6000])
def test_terminal_shortfalls_have_no_bonus_or_cumulative_grade(ore, waste):
    r = request(pb.EPISODE_END, 1, 0, 28800)
    c = dict(r.reward_components)
    c.update(ore_tons_shift=ore, production_fraction_raw=ore/16000,
             production_shortfall=max(0, 1-ore/16000), production=-4*max(0, 1-ore/16000),
             waste_tons_shift=waste, waste_fraction_raw=waste/4000,
             waste_shortfall=max(0, 1-waste/4000), waste=-4*max(0, 1-waste/4000))
    validate_reward_accounting(sum(c[k] for k in ADDITIVE_COMPONENTS), c,
                               [window_summary_to_dict(w) for w in windows()])
    assert c['grade_shift'] == c['grade_action'] == 0
    assert c['production'] <= 0 and c['waste'] <= 0


@pytest.mark.parametrize('grade,violation', [(0.26,False),(0.28,False),(0.259,True),(0.281,True)])
def test_frozen_grade_interval(grade, violation):
    from python.reward_contract import grade_reward
    w = window_summary_to_dict(windows()[0])
    w.update(grade=grade, metal_tons=4000*grade, grade_gap=.27-grade,
             grade_reward_raw=grade_reward(.27-grade), grade_reward_weighted=grade_reward(.27-grade),
             violation_upper=grade > .28, violation_lower=grade < .26)
    validate_window_summary(w)
    assert (w['violation_upper'] or w['violation_lower']) == violation


def test_empty_window_is_violation_and_negative_grade_reward():
    w = window_summary_to_dict(windows()[0])
    w.update(ore_tons=0, metal_tons=0, grade=0, grade_gap=.27,
             grade_reward_raw=-1, grade_reward_weighted=-1, violation_lower=True)
    validate_window_summary(w)


@pytest.mark.parametrize('mutation', ['body', 'removed', 'added', 'observation'])
def test_reviewed_overlay_does_not_whitelist_unknown_changes(mutation):
    root, main, _ = load_alp(ROOT/'anylogic/DRL-PPO.alp')
    validate_alp_sources(root)
    functions = main.find('Functions')
    if mutation == 'added':
        f = ET.SubElement(functions, 'Function')
        ET.SubElement(f, 'Name').text = 'unreviewedFunction'
        ET.SubElement(f, 'Body').text = 'return;'
    else:
        name = 'buildPhysicalObservation' if mutation == 'observation' else 'selectNextLoadSiteAI'
        f = next(f for f in functions.findall('Function') if f.findtext('Name') == name)
        if mutation == 'removed':
            functions.remove(f)
        else:
            f.find('Body').text += '\n// unreviewed change'
    with pytest.raises(ValueError, match='changed'):
        validate_alp_sources(root)


def test_documented_three_parameter_migration_passes(tmp_path):
    root, _, _ = model()
    result = validate_alp_contract(write_model(tmp_path, root))
    assert result['reward_contract'] == REWARD_CONTRACT_ID
    assert result['reward_configuration'] == RewardConfiguration().to_dict()


@pytest.mark.parametrize('name,value', [('wGradeShift','6'), ('wGradeAction','0.15'),
                                      ('rewardContractId','"dispatch-reward-physical-v4"')])
def test_partial_migration_fails(tmp_path, name, value):
    root, main, _ = model()
    variable = next(v for v in main.findall('./Variables/Variable') if v.findtext('Name') == name)
    variable.find('./Properties/InitialValue/Code').text = value
    with pytest.raises(ValueError, match='contract|rewardContractId'):
        validate_alp_contract(write_model(tmp_path, root))
