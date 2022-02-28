import pandas as pd

class ProcessedEntry:
    def __init__(self,
                 doi: str,
                 uuid: str,
                 is_harvested: bool,
                 is_processed_softcite: bool,
                 is_processed_grobid: bool):
        self.doi: str = doi
        self.uuid: str = uuid
        self.is_harvested: bool = is_harvested
        self.is_processed_softcite: bool = is_processed_softcite
        self.is_processed_grobid: bool = is_processed_grobid

    def to_dataframe(self):
        return pd.DataFrame(
            {
                DOI: [self.doi],
                UUID: [self.uuid],
                IS_PROCESSED_SOFTCITE: [self.is_processed_softcite],
                IS_PROCESSED_GROBID: [self.is_processed_grobid],
            }
        )
