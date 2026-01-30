"""Parser for extracting structured watch data from descriptions."""

import re
from typing import Optional, Tuple


class WatchDescriptionParser:
    """Parses watch descriptions to extract structured data."""

    # Known watch brands
    BRANDS = [
        "rolex", "omega", "patek philippe", "audemars piguet", "cartier",
        "tag heuer", "breitling", "iwc", "jaeger-lecoultre", "panerai",
        "hublot", "zenith", "longines", "tissot", "seiko", "citizen",
        "tudor", "vacheron constantin", "a. lange & söhne", "blancpain",
        "chopard", "girard-perregaux", "ulysse nardin", "frank muller",
        "richard mille", "bulgari", "bvlgari", "montblanc", "rado",
        "hamilton", "oris", "bell & ross", "graham", "corum", "piaget",
        "maurice lacroix", "frederique constant", "movado", "raymond weil",
        "technomarine", "festina", "invicta", "fossil", "michael kors",
        "guess", "armani", "diesel", "swatch", "casio", "orient",
        "constantino", "technos", "magnum", "seculus", "mondaine",
        "champion", "dumont", "lince", "condor", "mormaii"
    ]

    # Material patterns
    MATERIALS = {
        "ouro rosa": ["ouro rosa", "rose gold", "rosê", "rose"],
        "ouro amarelo": ["ouro amarelo", "yellow gold", "ouro 18k", "ouro 750"],
        "ouro branco": ["ouro branco", "white gold"],
        "ouro": ["ouro", "gold"],
        "aço e ouro": ["aço e ouro", "steel and gold", "aço/ouro", "bicolor", "two-tone", "rolesor"],
        "aço": ["aço", "steel", "aço inox", "aço inoxidável", "stainless steel"],
        "titânio": ["titânio", "titanium"],
        "platina": ["platina", "platinum"],
        "cerâmica": ["cerâmica", "ceramic"],
        "prata": ["prata", "silver"],
        "bronze": ["bronze"],
    }

    # Bracelet material patterns
    BRACELET_MATERIALS = {
        "aço": ["pulseira de aço", "bracelete de aço", "pulseira aço", "steel bracelet"],
        "couro": ["pulseira de couro", "couro", "leather", "couro legítimo", "crocodilo", "jacaré"],
        "borracha": ["pulseira de borracha", "borracha", "rubber", "silicone"],
        "ouro": ["pulseira de ouro", "bracelete de ouro", "pulseira ouro"],
        "tecido": ["pulseira de tecido", "nato", "nylon", "tecido"],
        "aço e ouro": ["pulseira aço e ouro", "pulseira bicolor"],
    }

    def parse(self, description: str) -> dict:
        """
        Parse a watch description and extract structured data.

        Returns dict with keys: brand, year, model, specification,
        material, weight, bracelet_material
        """
        if not description:
            return {}

        desc_lower = description.lower()

        result = {
            "brand": self._extract_brand(desc_lower, description),
            "year": self._extract_year(description),
            "model": self._extract_model(description),
            "specification": self._extract_specification(description),
            "material": self._extract_material(desc_lower),
            "weight": self._extract_weight(description),
            "bracelet_material": self._extract_bracelet_material(desc_lower),
        }

        return result

    def _extract_brand(self, desc_lower: str, original: str) -> str:
        """Extract watch brand from description."""
        for brand in self.BRANDS:
            if brand in desc_lower:
                # Return with proper capitalization
                idx = desc_lower.find(brand)
                return original[idx:idx+len(brand)].strip()
        return ""

    def _extract_year(self, description: str) -> Optional[int]:
        """Extract year from description."""
        # Look for 4-digit years between 1900-2030
        patterns = [
            r'\b(19[0-9]{2}|20[0-2][0-9])\b',  # General year
            r'ano[:\s]+(\d{4})',  # "ano: 2020" or "ano 2020"
            r'fabricação[:\s]+(\d{4})',  # "fabricação: 2020"
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2030:
                    return year
        return None

    def _extract_model(self, description: str) -> str:
        """Extract model name/number from description."""
        patterns = [
            r'modelo[:\s]+([^\n,\.]+)',
            r'ref\.?\s*[:\s]*([A-Z0-9\-\.]+)',
            r'referência[:\s]+([^\n,\.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Try to find model numbers like "116500LN", "5711/1A"
        model_pattern = r'\b([A-Z]{0,3}\d{3,6}[A-Z]{0,4}(?:/\d{1,2}[A-Z]?)?)\b'
        match = re.search(model_pattern, description)
        if match:
            return match.group(1)

        return ""

    def _extract_specification(self, description: str) -> str:
        """Extract specifications (movement, size, etc.)."""
        specs = []

        # Movement type
        movement_patterns = [
            (r'(automático|automatic)', "Automático"),
            (r'(manual|corda manual)', "Corda manual"),
            (r'(quartz|quartzo)', "Quartzo"),
            (r'(cronógrafo|chronograph)', "Cronógrafo"),
        ]

        for pattern, name in movement_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                specs.append(name)

        # Case size
        size_match = re.search(r'(\d{2,3})\s*mm', description, re.IGNORECASE)
        if size_match:
            specs.append(f"{size_match.group(1)}mm")

        # Water resistance
        wr_match = re.search(r'(\d+)\s*(m|atm|bar)\b', description, re.IGNORECASE)
        if wr_match:
            specs.append(f"WR {wr_match.group(1)}{wr_match.group(2)}")

        return ", ".join(specs)

    def _extract_material(self, desc_lower: str) -> str:
        """Extract case material."""
        # Check for combined materials first (more specific)
        if any(m in desc_lower for m in self.MATERIALS["aço e ouro"]):
            return "Aço e ouro"

        if any(m in desc_lower for m in self.MATERIALS["ouro rosa"]):
            return "Ouro rosa"

        if any(m in desc_lower for m in self.MATERIALS["ouro amarelo"]):
            return "Ouro amarelo"

        if any(m in desc_lower for m in self.MATERIALS["ouro branco"]):
            return "Ouro branco"

        for material_name, patterns in self.MATERIALS.items():
            if material_name in ["ouro rosa", "ouro amarelo", "ouro branco", "aço e ouro"]:
                continue  # Already checked
            for pattern in patterns:
                if pattern in desc_lower:
                    return material_name.capitalize()

        return ""

    def _extract_weight(self, description: str) -> str:
        """Extract weight from description."""
        patterns = [
            r'peso[:\s]+(\d+[,.]?\d*)\s*(g|gr|gramas|kg)',
            r'(\d+[,.]?\d*)\s*(g|gr|gramas)\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                weight = match.group(1).replace(',', '.')
                unit = match.group(2).lower()
                if unit in ['g', 'gr', 'gramas']:
                    return f"{weight}g"
                elif unit == 'kg':
                    return f"{weight}kg"

        return ""

    def _extract_bracelet_material(self, desc_lower: str) -> str:
        """Extract bracelet/strap material."""
        for material_name, patterns in self.BRACELET_MATERIALS.items():
            for pattern in patterns:
                if pattern in desc_lower:
                    return material_name.capitalize()
        return ""
