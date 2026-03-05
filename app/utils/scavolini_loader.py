"""Scavolini transcodification table loader using pandas."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List


class ScavoliniTranscodificationLoader:
    """Loads and queries the Scavolini transcodification table."""
    
    def __init__(self, xlsx_path: str = "transcoding/Tabella transcodifica Scavolini 13.02.26.xlsx"):
        """
        Initialize the loader.
        
        Args:
            xlsx_path: Path to the Scavolini transcodification Excel file
        """
        self.xlsx_path = Path(xlsx_path)
        self._df: Optional[pd.DataFrame] = None
        self._columns: Optional[List[str]] = None
    
    def load_columns_only(self) -> List[str]:
        """
        Load only the column names from the Excel file without loading all data.
        
        Returns:
            List of column names
        """
        if self._columns is None:
            # Read only the first row to get column names
            df_sample = pd.read_excel(self.xlsx_path, nrows=0)
            self._columns = df_sample.columns.tolist()
        
        return self._columns
    
    def load_data(self) -> pd.DataFrame:
        """
        Load the full transcodification table.
        
        Returns:
            DataFrame with transcodification data
        """
        if self._df is None:
            print(f"Loading Scavolini transcodification table from {self.xlsx_path}...")
            self._df = pd.read_excel(self.xlsx_path)
            print(f"Loaded {len(self._df)} rows with {len(self._df.columns)} columns")
        
        return self._df
    
    def get_column_info(self) -> Dict[str, str]:
        """
        Get information about each column.
        
        Returns:
            Dictionary mapping column names to their data types
        """
        columns = self.load_columns_only()
        
        # Load a small sample to get data types
        df_sample = pd.read_excel(self.xlsx_path, nrows=10)
        
        column_info = {}
        for col in columns:
            dtype = str(df_sample[col].dtype)
            column_info[col] = dtype
        
        return column_info
    
    def lookup_mago4_code(
        self,
        mat_piano: Optional[str] = None,
        col_piano: Optional[str] = None,
        fin_piano: Optional[str] = None,
        prof_piano: Optional[str] = None,
        cod_art_cliente: Optional[str] = None
    ) -> Optional[str]:
        """
        Lookup Mago4 code based on Scavolini attributes.
        
        Args:
            mat_piano: Material code (C_MATPIANO)
            col_piano: Color code (C_COLPIANO)
            fin_piano: Finish code (C_FINPIANO)
            prof_piano: Profile code (C_PROFPIANO)
            cod_art_cliente: Customer article code
            
        Returns:
            Mago4 code if found, None otherwise
        """
        df = self.load_data()
        
        # Build query conditions
        conditions = []
        
        if mat_piano:
            conditions.append(f"C_MATPIANO == '{mat_piano}'")
        if col_piano:
            conditions.append(f"C_COLPIANO == '{col_piano}'")
        if fin_piano:
            conditions.append(f"C_FINPIANO == '{fin_piano}'")
        if prof_piano:
            conditions.append(f"C_PROFPIANO == '{prof_piano}'")
        if cod_art_cliente:
            conditions.append(f"COD_ART_CLIENTE == {cod_art_cliente}")
        
        if not conditions:
            return None
        
        # Combine conditions with AND
        query = " & ".join(conditions)
        
        try:
            result = df.query(query)
            
            if len(result) > 0:
                # Return the CodiceFinaleMago from the first match
                mago4_code = result.iloc[0]['CodiceFinaleMago']
                if pd.notna(mago4_code):
                    return str(mago4_code)
            
            return None
            
        except Exception as e:
            print(f"Error querying transcodification table: {e}")
            return None
    
    def search_by_attributes(self, attributes: Dict[str, str]) -> pd.DataFrame:
        """
        Search for matching rows based on a dictionary of attributes.
        
        Args:
            attributes: Dictionary of attribute names and values
            
        Returns:
            DataFrame with matching rows
        """
        df = self.load_data()
        
        # Build query
        conditions = []
        for key, value in attributes.items():
            if value:
                conditions.append(f"{key} == '{value}'")
        
        if not conditions:
            return pd.DataFrame()
        
        query = " & ".join(conditions)
        
        try:
            return df.query(query)
        except Exception as e:
            print(f"Error searching: {e}")
            return pd.DataFrame()


# Singleton instance
_loader_instance: Optional[ScavoliniTranscodificationLoader] = None


def get_scavolini_loader() -> ScavoliniTranscodificationLoader:
    """Get or create the singleton loader instance."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ScavoliniTranscodificationLoader()
    return _loader_instance


if __name__ == "__main__":
    # Test script to show column names
    loader = ScavoliniTranscodificationLoader()
    
    print("=== Scavolini Transcodification Table ===\n")
    
    print("Column Names:")
    columns = loader.load_columns_only()
    for i, col in enumerate(columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\nTotal columns: {len(columns)}")
    
    print("\n=== Column Data Types ===\n")
    column_info = loader.get_column_info()
    for col, dtype in column_info.items():
        print(f"  {col}: {dtype}")
