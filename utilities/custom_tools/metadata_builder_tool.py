import pandas as pd
import json
import gc
from typing import List, Dict
from typing import Optional
from agno.tools import Toolkit


config = {
    "FNWL.FAST.HOLDING.HOLDING": {
        "sheet":{
        "N":{"NAME":"Rules Mapping", "COLS":"'MVP#','Target Filename','Attribute Name (ACORD)','FAST Rules & Transformations','FAST Table Name', 'FAST Column Name'"},
        "S":{"NAME":"ODH Mapping", "COLS":"'Source Extract','Source column','AttributeName','Lookup table','Lookup on _id','What Goes in'"}
        },
        "dynamoDB": {
        "N":{"Table":"LAKE.POLICYPARTY.ODHFNWL.JOB.METADATA","JobID":"DL-POLICYPARTY-ODHFNWL-FAST-BB-INITIAL-HOLDING-ERER"},
        "S":{"Table":"LAKE.POLICYPARTY.ODHFNWL.JOB.METADATA","JobID":"DL-POLICYPARTY-ODHFNWL-FAST-BB-HOLDING-EREL"}
        },
        "s3": {
        "MAPPING_FILE":{ "BUCKET":"rlus-productlife-genai-sdlc-poc-bucket", "PATH":"mapping-docs/ODH_Holding-Holding_FAST_NEW.xlsx" }
        },
        "local_path": ""
    }
}


class MetadataBuilderTools(Toolkit):
    def __init__(self, **kwargs):
        super().__init__(name="excel_metadata_tools", 
                        tools=[self.extract_metadata_from_excel], 
                        **kwargs)

    def extract_metadata_from_excel(self, file_path: str):
        """
        Extracts metadata from an Excel file based on specific transformations and filtering.
        
        Args:
            file_path (str): Path to the Excel file to process
            
        Returns:
            List[Dict[str, str]: Processed metadata in json specified format, or None if error occurs
        """

        target_file = "FNWL.FAST.HOLDING.HOLDING"
        try:
            df = pd.read_excel(
                file_path, 
                sheet_name=config[target_file]['sheet']['N']['NAME'], 
                usecols=[item.strip().strip("'") for item in (config[target_file]['sheet']['N']['COLS']).split(',')], 
                skiprows=1
            )
            
            # Apply filters
            df = df[df['Target Filename'].isin([target_file])]
            df = df[df['MVP#'].isin([1, '1S'])]
            df['FAST Rules & Transformations'] = df['FAST Rules & Transformations'].astype(str)

            metadata_json = df.apply(lambda x: {
                "Attribute": str.lower(x['Attribute Name (ACORD)']),
                "Rules": "'" + str(x['FAST Rules & Transformations']).split('DELTA', 1)[0] + "'",
                "Path": "'" + str(x['FAST Table Name']) + "." + str(x['FAST Column Name']) + "'"
            }, axis=1).tolist()
            
            print(metadata_json)
            return metadata_json
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return None
            
        finally:
            if 'df' in locals():
                del df
            if 'metadata' in locals():
                del metadata
            gc.collect()