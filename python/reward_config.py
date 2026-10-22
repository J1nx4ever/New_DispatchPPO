"""Configuration identity for paired physical-v4 reward ablations."""
from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite

@dataclass(frozen=True)
class RewardConfiguration:
    grade_action_enabled: bool = False
    waste_shortfall_weight: float = 4.0
    waste_target_tons: float = 4000.0

    def __post_init__(self):
        if type(self.grade_action_enabled) is not bool:
            raise ValueError('grade_action_enabled must be bool')
        if any(not isfinite(v) or v < 0 for v in (self.waste_shortfall_weight,self.waste_target_tons)):
            raise ValueError('waste reward parameters must be finite and nonnegative')
        object.__setattr__(self,'waste_shortfall_weight',float(self.waste_shortfall_weight))
        object.__setattr__(self,'waste_target_tons',float(self.waste_target_tons))

    @property
    def variant(self):
        return 'grade-action-on' if self.grade_action_enabled else 'grade-action-off'

    def to_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        from .reward_contract import REWARD_CONTRACT_ID, FROZEN_REWARD_PARAMETERS
        payload=dict(contract=REWARD_CONTRACT_ID,parameters=FROZEN_REWARD_PARAMETERS,**asdict(self))
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


# These are metadata in the existing reward_components map, never additive rewards.
RUNTIME_PREFIX = 'config.'


def configuration_from_components(components):
    """Read a self-contained RPC configuration; never consult an ALP file.

    v4 math constants must match its known contract. The ablation switch, waste
    target and waste weight come from AnyLogic. No parameter is inferred from a
    zero terminal penalty (which would not identify its weight).
    """
    from .reward_contract import FROZEN_REWARD_PARAMETERS
    required = {RUNTIME_PREFIX+k for k in FROZEN_REWARD_PARAMETERS}
    required.update({'grade_action_enabled','config.waste_shortfall_weight'})
    missing = required.difference(components)
    if missing:
        raise ValueError('AnyLogic runtime configuration missing: '+', '.join(sorted(missing)))
    if any(not isfinite(float(components[k])) for k in required):
        raise ValueError('AnyLogic runtime configuration contains non-finite values')
    flag = components['grade_action_enabled']
    if flag not in (0,1):
        raise ValueError('grade_action_enabled must be zero or one')
    for key, expected in FROZEN_REWARD_PARAMETERS.items():
        if key == 'target_waste_tons_shift':
            continue
        actual = float(components[RUNTIME_PREFIX+key])
        if abs(actual-expected) > 1e-9:
            raise ValueError(f'unsupported v4 runtime parameter {key}={actual}; expected {expected}')
    return RewardConfiguration(bool(flag),float(components['config.waste_shortfall_weight']),
                               float(components['config.target_waste_tons_shift']))


def configuration_to_components(config):
    """Wire metadata serializer for clients/tests; not an ALP source reader."""
    from .reward_contract import FROZEN_REWARD_PARAMETERS
    values = {RUNTIME_PREFIX+k:float(v) for k,v in FROZEN_REWARD_PARAMETERS.items()}
    values.update({'grade_action_enabled':float(config.grade_action_enabled),
                   'config.waste_shortfall_weight':float(config.waste_shortfall_weight),
                   'config.target_waste_tons_shift':float(config.waste_target_tons)})
    return values
