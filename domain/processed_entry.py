from collections.abc import Sequence


class ProcessedEntry(Sequence):
    def __init__(self,
                 doi: str,
                 uuid: str,
                 is_harvested: str,
                 is_processed_softcite: str,
                 is_processed_grobid: str,
                 harvester_used: str,
                 domain: str,
                 url_used: str):
        self.doi: str = doi
        self.uuid: str = uuid
        self.is_harvested: str = is_harvested
        self.is_processed_softcite: str = is_processed_softcite
        self.is_processed_grobid: str = is_processed_grobid
        self.harvester_used: str = harvester_used
        self.domain: str = domain
        self.url_used: str = url_used
        self._tup = (self.doi, self.uuid, self.is_harvested, self.is_processed_softcite, self.is_processed_grobid,
                     self.harvester_used, self.domain, self.url_used)

    def __repr__(self) -> str:
        return str(self._tup)

    def __getitem__(self, i):
        return self._tup[i]

    def __len__(self):
        return len(self._tup)
