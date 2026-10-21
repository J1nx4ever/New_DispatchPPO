"""Experiment override regression tests use temporary ALP copies only."""
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from python.alp_audit import experiment_value, load_alp, validate_alp_contract

ROOT = Path(__file__).resolve().parents[1]


def model():
    root, main, _ = load_alp(ROOT / 'anylogic/DRL-PPO.alp')
    experiment = next(e for e in root.iter('ParamVariationExperiment')
                      if e.findtext('Name') == 'RL_Training')
    return root, main, experiment


def override(main, experiment, name, code, tag='FreeformParamValue'):
    variable = next(v for v in main.findall('./Variables/Variable') if v.findtext('Name') == name)
    entry = next((e for e in experiment.findall(tag) if e.findtext('Id') == variable.findtext('Id')), None)
    if entry is None:
        entry = ET.SubElement(experiment, tag)
        ET.SubElement(entry, 'Id').text = variable.findtext('Id')
    expression = entry.find('Expression')
    if expression is None:
        expression = ET.SubElement(entry, 'Expression', Class='CodeValue')
    node = expression.find('Code')
    if node is None:
        node = ET.SubElement(expression, 'Code')
    node.text = code
    return entry


def write_model(tmp_path, root):
    path = tmp_path / 'fixture.alp'
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)
    return path


def test_freeform_true_overrides_false_default(tmp_path):
    root, main, exp = model()
    variable = next(v for v in main.findall('./Variables/Variable') if v.findtext('Name') == 'usePhysicalObservation')
    variable.find('./Properties/DefaultValue/Code').text = 'false'
    override(main, exp, 'usePhysicalObservation', 'true')
    override(main, exp, 'deterministicCheck', 'false')
    assert experiment_value(main, exp, 'usePhysicalObservation') == 'true'
    result = validate_alp_contract(write_model(tmp_path, root))
    assert result['use_physical_observation'] and not result['deterministic_check']
    assert not result['alp_runtime_verified']


@pytest.mark.parametrize('code', ['fasle', 'TRUE', 'someJavaExpression()'])
def test_unverifiable_boolean_rejected(tmp_path, code):
    root, main, exp = model()
    override(main, exp, 'usePhysicalObservation', 'true')
    override(main, exp, 'deterministicCheck', code)
    with pytest.raises(ValueError, match='deterministicCheck'):
        validate_alp_contract(write_model(tmp_path, root))


def test_explicit_false_overrides_true_default(tmp_path):
    root, main, exp = model()
    variable = next(v for v in main.findall('./Variables/Variable') if v.findtext('Name') == 'usePhysicalObservation')
    variable.find('./Properties/DefaultValue/Code').text = 'true'
    override(main, exp, 'usePhysicalObservation', 'false')
    with pytest.raises(ValueError, match='disabled'):
        validate_alp_contract(write_model(tmp_path, root))


def test_only_active_variation_mode_applies():
    _, main, exp = model()
    exp.find('UseFreeformParameters').text = 'true'
    override(main, exp, 'usePhysicalObservation', 'true')
    entry = override(main, exp, 'usePhysicalObservation', 'false', 'RangeVariationParamValue')
    if entry.find('Type') is None:
        ET.SubElement(entry, 'Type').text = 'FIXED'
    else:
        entry.find('Type').text = 'FIXED'
    assert experiment_value(main, exp, 'usePhysicalObservation') == 'true'
    exp.find('UseFreeformParameters').text = 'false'
    assert experiment_value(main, exp, 'usePhysicalObservation') == 'false'
    entry.find('Type').text = 'RANGE'
    with pytest.raises(ValueError, match='varying parameter'):
        experiment_value(main, exp, 'usePhysicalObservation')


@pytest.mark.parametrize('code', ['0.25', 'NaN'])
def test_reward_parameter_override_checked(tmp_path, code):
    root, main, exp = model()
    override(main, exp, 'targetGrade', code)
    with pytest.raises(ValueError, match='targetGrade'):
        validate_alp_contract(write_model(tmp_path, root))
