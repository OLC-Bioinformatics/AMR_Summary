from amr_summary.amr_summary import AMRSummary, assert_path, cli
from unittest.mock import patch
import argparse
import pytest
import shutil
import os


@pytest.fixture(name='variables', scope='module')
def setup():
    class Variables:
        def __init__(self):
            # Extract the account name and connection string from the system keyring prior to running tests
            self.test_path = os.path.abspath(os.path.dirname(__file__))
            self.file_path = os.path.join(self.test_path, 'files')
            self.output_path = os.path.join(self.test_path, 'outputs')
            self.database_path = os.path.join(self.test_path, 'databases')

    return Variables()


def test_assert_test_path(variables):
    clean_path = assert_path(
        path_name=variables.test_path,
        category='test')
    assert clean_path == variables.test_path


def test_assert_test_path_no_category(variables):
    with pytest.raises(TypeError):
        assert_path(path_name=variables.test_path)


def test_assert_path_tilde():
    with pytest.raises(SystemExit):
        assert_path(
            path_name='~/fake-path',
            category='test')


def test_assert_database_variable(variables):
    variables.resfinder_path, variables.mob_recon_path = \
        AMRSummary.assert_databases(database_path=variables.database_path)
    assert variables.resfinder_path == os.path.join(variables.database_path, 'resfinder')


def test_assert_database_folder(variables):
    assert os.path.isdir(variables.resfinder_path)


def test_assert_database_files(variables):
    assert os.path.isfile(os.path.join(variables.resfinder_path, 'colistin.tfa'))


def test_assert_database_combined_targets(variables):
    assert os.path.getsize(os.path.join(variables.resfinder_path, 'combinedtargets.fasta')) > 100


def test_run_resfinder(variables):
    AMRSummary.run_resfinder(
        sequence_path=variables.file_path,
        database_path=variables.resfinder_path,
        report_path=variables.output_path)
    assert os.path.isfile(os.path.join(variables.output_path, 'resfinder_blastn.xlsx'))


def test_run_mob_recon(variables):
    AMRSummary.run_mob_recon(sequence_path=variables.file_path,
                             database_path=variables.mob_recon_path,
                             report_path=variables.output_path)
    assert os.path.isfile(os.path.join(variables.output_path, 'amr_summary.csv'))


@pytest.mark.parametrize('folder_name',
                         ['~/fake-path',
                          ''])
def test_amr_summary_class_reports(variables, folder_name):
    AMRSummary(sequence_path=variables.file_path,
               database_path=variables.database_path,
               report_path=folder_name)


def test_amr_summary_class_permissions_error(variables):
    if not os.environ.get('CIRCLECI'):
        with pytest.raises(SystemExit):
            report_path = '/invalid'
            AMRSummary(sequence_path=variables.file_path,
                       database_path=variables.database_path,
                       report_path=report_path)


@patch('argparse.ArgumentParser.parse_args')
def test_amr_summary_integration(mock_args, variables):
    report_path = os.path.join(variables.output_path, 'integration')
    mock_args.return_value = argparse.Namespace(sequence_path=variables.file_path,
                                                database_path=variables.database_path,
                                                report_path=report_path,
                                                debug=True)
    cli()
    assert os.path.isfile(os.path.join(report_path, 'resfinder_blastn.xlsx'))


def test_clean_databases(variables):
    shutil.rmtree(variables.database_path)
    assert not os.path.isdir(variables.database_path)


def test_remove_path():
    fake_path = '~/fake-path'
    shutil.rmtree(fake_path)
    assert not os.path.isdir(fake_path)


def test_remove_tilde_path():
    fake_path = os.path.join(os.getcwd(), '~')
    shutil.rmtree(fake_path)
    assert not os.path.isdir(fake_path)


def test_clean_outputs(variables):
    shutil.rmtree(variables.output_path)
    assert not os.path.isdir(variables.output_path)
