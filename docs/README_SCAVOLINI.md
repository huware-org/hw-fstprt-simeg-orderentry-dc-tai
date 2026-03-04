# Scavolini Transcodification Integration

This document explains how to use the Scavolini transcodification table with the order entry system.

## Overview

The Scavolini XML orders contain structured attributes that need to be mapped to internal Mago4 codes using a large Excel transcodification table.

## XML Structure

Scavolini XML files contain orders with characteristics like:

```xml
<CARATTERISTICHE>
    <CARATTERISTICA>
        <COD_NOME>C_MATPIANO</COD_NOME>
        <NOME>Materiale piano</NOME>
        <COD_VALORE>MP0047</COD_VALORE>
        <VALORE>Quarzite</VALORE>
    </CARATTERISTICA>
    <CARATTERISTICA>
        <COD_NOME>C_COLPIANO</COD_NOME>
        <NOME>Colore piano</NOME>
        <COD_VALORE>CP1291</COD_VALORE>
        <VALORE>Taj Mahal_Qzt</VALORE>
    </CARATTERISTICA>
    <CARATTERISTICA>
        <COD_NOME>C_FINPIANO</COD_NOME>
        <NOME>Finitura piano</NOME>
        <COD_VALORE>FP0207</COD_VALORE>
        <VALORE>Opaca_Qzt</VALORE>
    </CARATTERISTICA>
    <CARATTERISTICA>
        <COD_NOME>C_PROFPIANO</COD_NOME>
        <NOME>Profilo piano</NOME>
        <COD_VALORE>PP1083</COD_VALORE>
        <VALORE>3D59 -Sp 2 squadr.pieno -Qzt</VALORE>
    </CARATTERISTICA>
</CARATTERISTICHE>
```

## Key Attributes for Transcodification

The main attributes used for N:1 mapping are:

1. **C_MATPIANO** - Material code (e.g., MP0047 = Quarzite)
2. **C_COLPIANO** - Color code (e.g., CP1291 = Taj Mahal_Qzt)
3. **C_FINPIANO** - Finish code (e.g., FP0207 = Opaca_Qzt)
4. **C_PROFPIANO** - Profile code (e.g., PP1083 = 3D59 -Sp 2 squadr.pieno -Qzt)
5. **COD_ART_CLIENTE** - Customer article code (e.g., 77080023)

## Using the Scavolini Loader

### Inspect the Table Structure

To see the column names and structure without loading the full file:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the inspection script
python inspect_scavolini_table.py
```

This will show:
- All column names in the Excel file
- Data types for each column
- Which key columns are present
- Possible Mago4 code column names

### Using in Code

```python
from BE.scavolini_loader import get_scavolini_loader

# Get the singleton loader instance
loader = get_scavolini_loader()

# Lookup Mago4 code based on attributes
mago4_code = loader.lookup_mago4_code(
    mat_piano="MP0047",
    col_piano="CP1291",
    fin_piano="FP0207",
    prof_piano="PP1083",
    cod_art_cliente="77080023"
)

if mago4_code:
    print(f"Found Mago4 code: {mago4_code}")
else:
    print("No matching code found")
```

### Search with Partial Attributes

```python
# Search with only some attributes
results = loader.search_by_attributes({
    "C_MATPIANO": "MP0047",
    "C_COLPIANO": "CP1291"
})

print(f"Found {len(results)} matching rows")
```

## Integration with Main System

The Scavolini loader can be integrated into the main order processing workflow:

1. **XML Parsing**: Extract characteristics from XML
2. **Attribute Mapping**: Map XML characteristics to lookup keys
3. **Transcodification**: Query the Excel table using pandas
4. **Mago4 Code**: Return the matched internal code
5. **Flat Table**: Include in the Mago4 bridge table output

## Performance Considerations

- **First Load**: The Excel file is loaded once and cached in memory
- **Subsequent Queries**: Fast pandas DataFrame queries
- **Memory Usage**: The full table stays in memory after first load
- **Column-Only Mode**: Use `load_columns_only()` to inspect structure without loading data

## Example Workflow

```python
# 1. Parse XML order
import xml.etree.ElementTree as ET
tree = ET.parse('docs/inputs/3_124_5525059529_20251218.XML')
root = tree.getroot()

# 2. Extract characteristics for each item
for dettaglio in root.findall('.//DETTAGLIO'):
    caratteristiche = {}
    for car in dettaglio.findall('.//CARATTERISTICA'):
        cod_nome = car.find('COD_NOME').text
        cod_valore = car.find('COD_VALORE').text
        caratteristiche[cod_nome] = cod_valore
    
    # 3. Lookup Mago4 code
    loader = get_scavolini_loader()
    mago4_code = loader.lookup_mago4_code(
        mat_piano=caratteristiche.get('C_MATPIANO'),
        col_piano=caratteristiche.get('C_COLPIANO'),
        fin_piano=caratteristiche.get('C_FINPIANO'),
        prof_piano=caratteristiche.get('C_PROFPIANO'),
        cod_art_cliente=dettaglio.find('COD_ART_CLIENTE').text
    )
    
    print(f"Item: {dettaglio.find('DESC_ART_CLIENTE').text}")
    print(f"Mago4 Code: {mago4_code or 'NOT FOUND'}")
```

## Next Steps

1. Run `inspect_scavolini_table.py` to see the actual column structure
2. Update `scavolini_loader.py` with the correct Mago4 code column name
3. Integrate the loader into the main FastAPI backend
4. Add a second API endpoint for Scavolini XML processing
5. Update the Gradio UI to support both PDF and XML workflows
