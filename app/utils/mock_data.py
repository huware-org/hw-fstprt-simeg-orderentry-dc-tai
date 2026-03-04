"""Mock master data for prototype demonstration."""

# Customer Master Data
# Maps customer names to customer codes, payment terms, and addresses
mock_customers = {
    "MOLTENI&C. S.P.A.": {
        "code": "C-MOL",
        "payment_terms": "30gg DFFM",
        "address": "Via Rossini 50, 20833 Giussano (MB)"
    },
    "DV HOME S.R.L.": {
        "code": "C-DV",
        "payment_terms": "60gg DF",
        "address": "Via Industria 15, 31010 Mareno di Piave (TV)"
    },
    "VISIONNAIRE S.R.L.": {
        "code": "C-VIS",
        "payment_terms": "30gg DFFM",
        "address": "Via Emilia 123, 40068 San Lazzaro di Savena (BO)"
    },
    "Scavolini S.p.a.": {
        "code": "C-SCAV",
        "payment_terms": "30gg DFFM",
        "address": "Via Risara 60/70-74/78, 61025 Montelabbate (PU)"
    },
    "Ernestomeda S.p.A.": {
        "code": "C-ERNE",
        "payment_terms": "30gg DFFM",
        "address": "Via dell'Economia 1, 61025 Montelabbate (PU)"
    }
}

# Transcodification Table (N:1 mapping)
# Maps (base_code, color, thickness) tuples to Mago4 item codes
mock_transcodification = {
    ("BRECCIA", "CAPRAIA", "20mm"): "48NLPIOSM12ALZ",
    ("MARMO", "OROBICO ARABESCATO", "20mm"): "31CACDLU02SST014",
    ("CERAMICA", "NERO MARQUINA", "12mm"): "40SEGBLUM300440A0",
    ("MARMO", "CALACATTA", "20mm"): "45MRCALC20MM",
    ("GRANITO", "NERO ASSOLUTO", "30mm"): "50GRNERO30MM",
    ("CERAMICA", "BIANCO CARRARA", "12mm"): "38CERBCAR12MM",
}

# Price List
# Maps Mago4 item codes to standard unit prices (EUR)
mock_price_list = {
    "48NLPIOSM12ALZ": 1500.00,
    "31CACDLU02SST014": 2200.00,
    "40SEGBLUM300440A0": 850.00,
    "45MRCALC20MM": 1800.00,
    "50GRNERO30MM": 2500.00,
    "38CERBCAR12MM": 750.00,
}
