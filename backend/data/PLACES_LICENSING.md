# GeoNames Gazetteer Licensing and Attribution

## Source & License
- **Source**: [GeoNames](https://www.geonames.org/export/)
- **License**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Cost**: 100% Free, zero billing, zero subscriptions, zero paid API keys.

## Attribution Notice
This product includes geographical data sourced from GeoNames (https://www.geonames.org), licensed under the Creative Commons Attribution 4.0 License.

## Scope of Coverage
The local gazetteer database (`backend/data/places.db`, ~15 MB SQLite database) contains **68,806 geographical entities**:
1. **Countries & Territories (252)**: Complete coverage of all ISO sovereign countries and territories (e.g., Iceland, Japan, Madagascar, Norway, New Zealand, Brazil, India, etc.).
2. **Administrative Divisions (3,865)**: Primary first-order regions, provinces, and states worldwide (e.g., Bavaria, Germany; Île-de-France, France; Himachal Pradesh, India; California, United States; Ontario, Canada; Bali, Indonesia; Tuscany, Italy).
3. **Cities & Populated Places (64,675)**: All cities, towns, and national capitals worldwide with a population of 5,000 or greater. Suburban sections (arrondissements and sub-boroughs) are filtered to avoid clutter.
4. **Supplementary Tourist Gems**: Famous resort villages, UNESCO heritage sites, and iconic destinations with populations below 5,000 (e.g., Positano, Hallstatt, Oia, Fira, Lake Louise, Mont Saint-Michel, Giethoorn).

## Limitations & Free-Typing Fallback
- Tiny rural villages, hamlets, and obscure points of interest with populations under 5,000 that are not included in the gazetteer can still be entered directly by typing them into the destination field.
- The destination input supports manual text entry without requiring an autocomplete selection.
