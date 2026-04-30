# GeneAlias
[Report a bug](https://github.com/stemcellbioengineering/GeneAlias/issues)

Trying to plot gene expression using `scanpy` but it throws an error because a gene name you provided does not match the names in `adata.var_names`? You have to search online for gene aliases to find the one that matches your data.

__GeneAlias__ takes a list of genes and builds a dictionary of gene aliases from the [HUGO Gene Nomenclature Committee (HGNC)](https://www.genenames.org/) database. You query the dictionary with a gene alias and it gives you the symbol used in your `adata`. For example, say you're interested in the transcription factor _E2A_. The official symbol is _TCF3_ and, in this example, is the one used in your dataset. Querying with _E2A_, _ITF1_, _bHLHb21_, or any other recognized alias will return _TCF3_. 

## Installation
Clone the repository from https://github.com/stemcellbioengineering/GeneAlias/. Then open your terminal, navigate to the root directory (contains the `pyproject.toml` file), and run the command `pip install .` to install the package and dependencies.

It is recommended to install in a `conda` environment (ideally the one where `scanpy` is installed). Tested with Python 3.12 but should work with older versions. The only dependency not part of the Python Standard Library is `httplib2`.

## Usage
Once installed, the package can be used like any other Python library. The example below shows its intended usage.
```python
import scanpy as sc
from genealias import aliases as al

# Get the gene symbols used in your AnnData
genes = list(adata.var_names)

# Initialize the AliasDict
ad = al.AliasDict()

# Build the alias dictionary
ad.build(genes)

# Run the genes you want to plot through the dictionary.
# If your dataset uses the official names then the output will be PLOT_GENES=["CXCR4","FLT3"]
PLOT_GENES = ad(["CD184", "CD135"])

# Create plots with scanpy where the color is the gene expression. 
sc.pl.umap(adata, color=PLOT_GENES)

```
The HGNC API rate limits requests to 10 per second. Thus, calls to `ad.build(.)` with a very large number of genes may take awhile (~5 min for 3000 genes). Therefore, it is recommended to save the dictionary as `.json` for re-use.
```python
# Save to file
ad.save("path/to/file.json")

# Load saved file
ad.load("path/to/file.json")
```
If you're interested in other information from the HGNC database, a helper function is included to make requests through the API.
```python
from genealias import aliases as al
response = al.fetch_hgnc("TCF3", field="symbol")
```
The response is a complete `.json` formatted record for the gene. The field can be any searchable field definition from the [HGNC REST API](https://www.genenames.org/help/rest/).

## Application notes
- If you query a gene that is not present in the dictionary, it will skip that query rather than raise a KeyError. A message will be displayed altering you to this
- Dictionary queries are case-insensitive, so you don't need to remember the case of gene aliases like _bHLHb21_
- The dictionary cannot handle partial matches, so spelling must be correct.
- Currently only the approved gene symbol and alias symbols are searched in the HGNC database. Future versions could include ENSEMBL ID or other values if there is interest. 

## Contributions
Contributors are welcome! If you have an idea for a new feature you can [issue a pull request](https://github.com/stemcellbioengineering/GeneAlias/pulls).

## License
This project is licensed under the GNU General Public License v3.0.