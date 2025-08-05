from db import DotDict
import json
from typing import Optional

class Parser:
    def __init__(self, source: str):
        self.source = source

    @property
    def formatted_text(self):
        return self.source

    @property
    def bold(self):
        return "**"

    @property
    def cursive(self):
        return "~~"

    @property
    def underline(self):
        return "__"
        
    def parse(self) -> Optional[str]: # json str
        bold_data = self._format(self.bold, "bold")
        cursive_data = self._format(self.cursive, "italic")
        underline_data = self._format(self.underline, "underline")

        data = bold_data + cursive_data + underline_data
        if not data:
            return None
        
        format_data = {"version": "1", "items": data}
        return json.dumps(format_data)

    def _trim(self, frm, add_to) -> str:
        return self.source[:frm] + self.source[frm + add_to:]
    
    def _format(self, symbol, type_name) -> list[dict]:
        ret = []
        
        ssym = self.source.find(symbol)
        while ssym != -1:
            self.source = self._trim(ssym, len(symbol))
            esym = self.source.find(symbol)
            self.source = self._trim(esym, len(symbol))
            
            el = DotDict()
            el.type = type_name
            el.offset = ssym
            el.length = esym - ssym
            
            ret.append(el)
            ssym = self.source.find(symbol)

        return ret
