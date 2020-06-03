import requests
import argparse
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import re

class RequestClient:
    def __init__(self, jwt=None):
        self.jwt = jwt
        self.headers = {
            'Content-Type': "application/json"
        }
        if jwt:
            self.headers['Authorization'] = 'Bearer '+jwt

    def get(self, url):
        resp = RequestClient.requests_retry_session().get(url, headers=self.headers)
        return RequestClient.process_response(resp)

    @classmethod
    def process_response(cls, resp):
        if (resp.status_code >= 400):
            raise Exception("HttpError[%s]: %s" % (resp.status_code, resp.content))
        return json.loads(resp.content)

    @classmethod
    def requests_retry_session(cls,
                               retries=8,
                               backoff_factor=0.3,
                               status_forcelist=(500, 502, 504),
                               session=None):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

def parse():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--jwt', dest='jwt', required=True, help='JWT for calling against clinical')
    parser.add_argument('--song-url', dest='song_url', required=True, help='song server url')
    parser.add_argument('--clinical-url', dest='clinical_url', required=True, help='clinical server url')
    return parser.parse_args()

class SongClient:
    def __init__(self, url):
        self.url = url
        self.client = RequestClient()

    def list_study_ids(self):
        return self.client.get(self.url+'/studies/all')

    def get_study_tree(self, study_id):
        return self.client.get(self.url+'/studies/'+study_id+'/all')

class ClinicalClient:
    def __init__(self, url, jwt):
        self.url = url
        self.client = RequestClient(jwt=jwt)

    def get_donors(self, study_id):
        return self.client.get(self.url+'/clinical/donors?programId='+study_id)

class DiffReport:
    def __init__(self, study_id):
        self.study_id = study_id
        self.donor_ids_missing_in_song = []
        self.sample_ids_missing_in_song = []
        self.specimen_ids_missing_in_song = []

    def add_missing_donor(self, donor_id):
        self.donor_ids_missing_in_song.append(donor_id)

    def add_missing_specimen(self, specimen_id):
        self.specimen_ids_missing_in_song.append(specimen_id)

    def add_missing_sample(self, sample_id):
        self.sample_ids_missing_in_song.append(sample_id)

    def has_missing_donors(self):
        return len(self.donor_ids_missing_in_song) > 0

    def has_missing_specimens(self):
        return len(self.specimen_ids_missing_in_song) > 0

    def has_missing_samples(self):
        return len(self.sample_ids_missing_in_song) > 0

    def to_dict(self):
        return {
            "studyId": self.study_id,
            "donors" : {
                "status" : "OK" if not self.has_missing_donors() else "ERROR",
                "missing" : self.donor_ids_missing_in_song
            },
            "specimens": {
                "status": "OK" if not self.has_missing_specimens() else "ERROR",
                "missing": self.specimen_ids_missing_in_song
            },
            "samples": {
                "status": "OK" if not self.has_missing_samples() else "ERROR",
                "missing": self.sample_ids_missing_in_song
            }
        }


class AuditData:
    def __init__(self):
        self.donor_ids = {}
        self.specimen_ids = {}
        self.sample_ids = {}

    def add_donor(self, donor_id):
        self.donor_ids[donor_id] = True

    def add_specimen(self, specimen_id):
        self.specimen_ids[specimen_id] = True

    def add_sample(self, sample_id):
        self.sample_ids[sample_id] = True


class Differ:
    def __init__(self, song_client, clinical_client):
        self.song_client = song_client
        self.clinical_client = clinical_client

    def generate_reports(self):
        reports = []
        for study_id  in self.song_client.list_study_ids():
            reports.append(self.get_song_data_not_in_clinical(study_id).to_dict())
        return reports

    def get_song_data_not_in_clinical(self, study_id):
        song_data = self.get_song_audit_data(study_id)
        clinical_data = self.get_clinical_audit_data(study_id)

        missing_donors = self.difference(song_data.donor_ids, clinical_data.donor_ids)
        missing_specimens = self.difference(song_data.specimen_ids, clinical_data.specimen_ids)
        missing_samples = self.difference(song_data.sample_ids, clinical_data.sample_ids)
        report = DiffReport(study_id)
        report.donor_ids_missing_in_song = list(missing_donors.keys())
        report.specimen_ids_missing_in_song = list(missing_specimens.keys())
        report.sample_ids_missing_in_song = list(missing_samples.keys())
        return report

    def get_clinical_audit_data(self, study_id):
        clinical_data = self.clinical_client.get_donors(study_id)
        data = AuditData()
        if clinical_data:
            for donor in clinical_data:
                full_donor_id = 'DO'+str(donor['donorId'])
                data.add_donor(full_donor_id)

                if "specimens" in donor:
                    for sp in donor['specimens']:
                        full_specimen_id = 'SP' + str(sp['specimenId'])
                        data.add_specimen(full_specimen_id)

                        if "samples" in sp:
                            for sa in sp['samples']:
                                full_sample_id = 'SA' + str(sa['sampleId'])
                                data.add_sample(full_sample_id)
        return data

    def get_song_audit_data(self, study_id):
        song_data = self.song_client.get_study_tree(study_id)
        data = AuditData()
        if 'donors' in song_data:
            for donor in song_data['donors']:
                full_donor_id = donor['donorId']
                data.add_donor(full_donor_id)

                if "specimens" in donor:
                    for sp in donor['specimens']:
                        full_specimen_id = sp['specimenId']
                        data.add_specimen(full_specimen_id)

                        if "samples" in sp:
                            for sa in sp['samples']:
                                full_sample_id = sa['sampleId']
                                data.add_sample(full_sample_id)
        return data



    def difference(self, left_dict, right_dict):
        return {k: left_dict[k] for k in set(left_dict) - set(right_dict)}



def main():
    parsed_args = parse()
    song_client = SongClient(parsed_args.song_url)
    clinical_client = ClinicalClient(parsed_args.clinical_url, parsed_args.jwt)
    differ = Differ(song_client, clinical_client)
    reports = differ.generate_reports()
    print(json.dumps(reports))
    sys.exit(0)


if __name__ == '__main__':
    main()
