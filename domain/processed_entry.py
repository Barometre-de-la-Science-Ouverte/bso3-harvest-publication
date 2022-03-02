from collections.abc import Sequence

class ProcessedEntry(Sequence):
    def __init__(self,
                 doi: str,
                 uuid: str,
                 is_harvested: bool,
                 is_processed_softcite: bool,
                 is_processed_grobid: bool):
        self.doi: str = doi
        self.uuid: str = uuid
        self.is_harvested: int = int(is_harvested)
        self.is_processed_softcite: int = int(is_processed_softcite)
        self.is_processed_grobid: int = int(is_processed_grobid)
        self._tup = (self.doi, self.uuid, self.is_harvested, self.is_processed_softcite, self.is_processed_grobid)

    def __repr__(self) -> str:
        return str(self._tup)

    def  __getitem__(self,i):
        return self._tup[i]

    def __len__(self):
        return len(self._tup)
