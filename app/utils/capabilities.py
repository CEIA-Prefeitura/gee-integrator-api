from datetime import datetime
CAPABILITIES = {
    "collections": [
        {
            "name": "s2_harmonized",
            "visparam": ["s2-green", "s2-red", "s2-rgb"],
            "period": ["WET", "DRY", "MONTH"],
            "year": list(range(2017, datetime.now().year + 1)),
        },
        {
            "name": "landsat",
            "visparam": ["landsat-true", "landsat-agri", "landsat-false"],
            "month": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
            "year": list(range(1985, datetime.now().year + 1)),
            "period": ["WET", "DRY", "MONTH"]
        }
    ]
}
