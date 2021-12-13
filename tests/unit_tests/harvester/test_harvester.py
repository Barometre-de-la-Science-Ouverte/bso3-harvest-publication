from unittest import TestCase, mock
import unittest
import gzip

from harvester.OAHarvester import _count_entries, _sample_selection


class HarvesterCountEntries(TestCase):

    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):

        wrong_filepath = 'wrong_filepath'

        with self.assertRaises(FileNotFoundError):
            _count_entries(open, wrong_filepath)

    def test_when_2_publications_then_return_2(self):
        filepath_2_publications = 'dump_2_publications.jsonl.gz'

        nb_publications = _count_entries(gzip.open, filepath_2_publications)

        self.assertEqual(nb_publications, 2)


class HarvesterSampleSelection(TestCase):

    def test_when_sample_is_4_then_return_list_of_size_4(self):
        sample = 22
        count = 4
        samples = _sample_selection(sample, count)
        self.assertEqual(len(samples), sample)

    def test_when_sample_is_0_then_raise_index_error_exception(self):
        sample = 0
        count = 4
        with self.assertRaises(IndexError):
            samples = _sample_selection(sample, count)



class HarvestUnpaywall(TestCase):

    def test_when_(self):
        # Given
        a = 5

        # When
        b = 5

        # Then
        pass

"""
    @mock.patch.object(PredictionML, '_from')
    @mock.patch.object(TicketAdapter, 'update_prediction_ml')
    @mock.patch.object(PredictionAdapter, 'write')
    @mock.patch('requests.patch')
    @mock.patch.object(Model, 'predict')
    @mock.patch.object(ModelAdapter, 'load')
    @mock.patch.object(TicketAdapter, 'get_tickets_to_predict')
    def test_when_no_papers_to_harvest_then_return_(
            self,
            mock_get_tickets_to_predict,
            mock_load_model,
            mock_predict,
            mock_requests_patch,
            mock_prediction_write,
            mock_update_prediction_ml,
            mock_retour_prediction_ml):
        # Given
        harvester: OAHarvester = harvester_no_papers_to_harvest.load_papers()

        mock_get_tickets_to_predict.return_value = [ticket_to_predict]
        mock_load_model.return_value = model_loader_test.load()
        mock_predict.return_value = VALEUR_TICKET_NON_PERTINENT
        mock_retour_prediction_ml.return_value = PredictionML.NON_PERTINENT

        # When
        prediction_result: int = perform_prediction()

        # Then
        prediction_expected = PredictionML._from(VALEUR_TICKET_NON_PERTINENT).value
        data: str = "{\"u_prediction_ml\":\"" + RetourServiceNow.NON_PERTINENT.value + "\"}"

        mock_prediction_write.assert_called()
        mock_update_prediction_ml.assert_called_with(ticket_to_predict.sys_id, prediction_expected)

        mock_requests_patch.assert_called_with(url=URL_BYNOW + ticket_to_predict.sys_id,
                                               auth=(SERVICE_NOW_LOGIN, SERVICE_NOW_PWD),
                                               headers=HEADERS,
                                               proxies={'https': None},
                                               data=data)

        self.assertEqual(prediction_result, 1)
"""

if __name__ == '__main__':
    unittest.main()
