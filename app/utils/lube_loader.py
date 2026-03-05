"""Lube transcodification table loader using pandas."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
from app.config.settings import logger


class LubeTranscodificationLoader:
    """Loads and queries the Lube transcodification table."""
    
    def __init__(self, xlsx_path: str = "transcoding/Tabella transcodifica Lube 13.02.26 (1).xlsx"):
        """
        Initialize the loader.
        
        Args:
            xlsx_path: Path to the Lube transcodification Excel file
        """
        self.xlsx_path = Path(xlsx_path)
        self._df: Optional[pd.DataFrame] = None
    
    def load_data(self) -> pd.DataFrame:
        """
        Load the full transcodification table.
        
        Returns:
            DataFrame with transcodification data
        """
        if self._df is None:
            logger.info(f"Loading Lube transcodification table from {self.xlsx_path}")
            self._df = pd.read_excel(self.xlsx_path)
            
            # Preprocess: Split Caratteristica column to extract just the code
            if 'Caratteristica' in self._df.columns:
                # Extract code from "PREFIX=CODE" format
                self._df['CaratteristicaCode'] = self._df['Caratteristica'].apply(
                    lambda x: str(x).split('=')[1].strip() if pd.notna(x) and '=' in str(x) else None
                )
                logger.debug(f"Preprocessed Caratteristica column, extracted {self._df['CaratteristicaCode'].notna().sum()} codes")
            
            logger.info(f"Loaded {len(self._df)} rows with {len(self._df.columns)} columns")
        
        return self._df
    
    def lookup_mago4_code(
        self,
        codice_base: Optional[str] = None,
        caratteristica: Optional[str] = None
    ) -> Optional[str]:
        """
        Lookup Mago4 code based on Lube attributes.
        
        Args:
            codice_base: Base product code from Lube
            caratteristica: Characteristic code (just the CODE part, e.g., "KS06")
            
        Returns:
            Mago4 code if found, None otherwise
        """
        df = self.load_data()
        
        # Build query conditions
        conditions = []
        
        if codice_base:
            conditions.append(f"Codice == '{codice_base}'")
        
        if caratteristica:
            # Match against the extracted code (not the full "PREFIX=CODE")
            conditions.append(f"CaratteristicaCode == '{caratteristica}'")
        
        if not conditions:
            logger.warning("No lookup conditions provided for Lube transcodification")
            return None
        
        # Combine conditions with AND
        query = " & ".join(conditions)
        logger.debug(f"Lube lookup query: {query}")
        
        try:
            result = df.query(query)
            
            if len(result) > 0:
                # Return the Codice Mago from the first match
                mago4_code = result.iloc[0]['Codice Mago']
                if pd.notna(mago4_code):
                    logger.debug(f"Lube lookup successful: {mago4_code}")
                    return str(mago4_code)
            
            logger.debug(f"No Lube match found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error querying Lube transcodification table: {e}", exc_info=True)
            return None


# Singleton instance
_lube_loader_instance: Optional[LubeTranscodificationLoader] = None


def get_lube_loader() -> LubeTranscodificationLoader:
    """Get or create the singleton loader instance."""
    global _lube_loader_instance
    if _lube_loader_instance is None:
        _lube_loader_instance = LubeTranscodificationLoader()
    return _lube_loader_instance


if __name__ == "__main__":
    # Test script
    loader = LubeTranscodificationLoader()
    df = loader.load_data()
    
    print("=== Lube Transcodification Table ===\n")
    print(f"Columns: {df.columns.tolist()}\n")
    print(f"Total rows: {len(df)}\n")
    
    # Show sample data
    print("Sample rows:")
    print(df.head())
