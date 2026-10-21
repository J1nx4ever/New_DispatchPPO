import io
import json
import numpy as np
import pytest
from python.smoke_dispatch import first_legal_action, run_episode

@pytest.mark.parametrize('mask,expected', [([1,1,1,1],0),([0,0,1,1],2),([0,0,0,1],3)])
def test_select_only_legal_actions(mask, expected):
    assert first_legal_action(mask)==expected

@pytest.mark.parametrize('mask', [[0,0,0,0],[1,0],[.5,1,0,0]])
def test_invalid_mask_rejected(mask):
    with pytest.raises(ValueError): first_legal_action(mask)


@pytest.mark.parametrize("record", [True, False])
def test_records_previous_action_and_stops_without_extra_reset(record):
    class SyntheticCallbacks:
        def __init__(self): self.resets=0; self.actions=[]
        def reset(self):
            self.resets+=1
            return np.zeros(1519,dtype=np.float32),dict(request_id='start',episode_id='test',action_mask=[0,1,1,0])
        def step(self,action):
            self.actions.append(action)
            terminal=len(self.actions)==2
            return np.full(1519,len(self.actions),dtype=np.float32),.25,terminal,False,dict(
                request_id='end' if terminal else 'decision',episode_id='test',
                action_mask=[0,0,0,0] if terminal else [0,0,0,1],previous_action=action)
    env=SyntheticCallbacks(); stream=io.StringIO()
    result=run_episode(env,stream if record else None,capture_observations=record)
    rows=[json.loads(line) for line in stream.getvalue().splitlines()]
    assert env.resets==1 and env.actions==[1,3]
    assert result['transitions']==2 and result['total_reward']==.5 and result['terminated']
    if not record:
        assert stream.getvalue()==''
        return
    assert rows[1]['action_request_id']=='start' and rows[1]['previous_action']==1
    assert rows[2]['action_request_id']=='decision' and rows[2]['previous_action']==3
    assert len(rows[0]['observation'])==1519
    assert result['observation_min']==[0]*1519 and result['observation_max']==[2]*1519
