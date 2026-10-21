import os
import time
import httplib2 as http
import json
from urllib.parse import urlparse



def fetch_hgnc(query:str, field:str = 'symbol') -> (dict | None):
    '''
    Fetches data from HUGO Gene Nomenclature Committee (HGNC) REST API for a given query and field.
    See https://www.genenames.org/help/rest/ for more information on the API.

    
    Parameters
    ----------
    query : str
        The query string to search for.
    field : str, optional
        The field to search in (default: 'symbol'). Can be 'symbol', 'alias_symbol', or other searchable fields.

        
    Returns
    -------
    dict | None
        The response from the HGNC API if the request was successful, None otherwise.
   
        
    Raises
    ------
    TypeError
        If query is not a string.
    TypeError
        If field is not a string.
    '''
    # Check that query and field are strings
    if not isinstance(query, str):
        raise TypeError('query must be a str')
    if not isinstance(field, str):
        raise TypeError('field must be a str')
    
    # Set up the request parameters
    headers = {'Accept': 'application/json',}
    uri = 'https://rest.genenames.org'
    path = '/fetch/' + field + '/' + query
    
    # Parse the URL and create an HTTP client
    target = urlparse(uri+path)
    method = 'GET'
    body = ''

    h = http.Http()

    # Make the request and get the response
    response, content = h.request(
    target.geturl(),
    method,
    body,
    headers)

    # If the request was successful, parse the content and return the response
    if response['status'] == '200':
        # Parse content with the json module 
        data = json.loads(content)
        return data['response']
    # If the request was not successful, print an error message and return None
    else:
        print('Error retrieving data for: {} (Error code: {})'.format(query, response['status']))
        return None

class AliasDict:

    def __init__(self) -> None:
        '''
        A dictionary for storing gene aliases and their corresponding symbols.

        
        Attributes
        ----------
        aliases : dict[str,str]
            A dictionary where keys are gene aliases and values are the corresponding gene symbols.
        '''
        self.aliases={}
        self._API_REQUEST_RATE = 0.1 # seconds

    def __call__(self, genes:list[str]) -> list[str]:
        '''
        Recieves a list of genes and/or gene aliases and returns a list of genes defined previously by the user

        
        Parameters
        ----------
        genes : list[str]
            A list of genes and/or gene aliases

        Returns
        -------
        list[str]
            A list of genes

        Raises
        ------
        TypeError
            If genes is not a list
        TypeError
            If elements in genes are not strings
        '''
        # Check that genes is a list/tuple of strings
        if not isinstance(genes, (list,tuple)):
            raise TypeError('genes must be a list or tuple of str')

        result = []
        for gene in genes:
            # Check that gene is a string
            if not isinstance(gene, str):
                raise TypeError('gene must be a str')
            
            # Get gene from alias dictionary
            try:
                result.append(self.aliases[gene.lower()])
            except KeyError:
                print('Gene not found: ' + gene)
        
        return result

    def build(self, genes:list[str]) -> None:
        '''
        Build a dictionary of gene aliases. If a dictionary 

        
        Parameters
        ----------
        genes : list[str]
            A list of genes to add to the dictionary

            
        Raises
        ------
        TypeError
            If genes is not a list
        TypeError
            If elements in genes are not strings
        '''
        # Check that genes is a list/tuple of strings
        if not isinstance(genes, (list,tuple)):
            raise TypeError('genes must be a list or tuple of str')

        idx = 1
        elapsed_time = 0

        # Iterate through genes and fetch data from HUGO
        for gene in genes:
            # Check that gene is a string and skip if not        
            if not isinstance(gene, str):
                print('genes must be type str, not: {}'.format(type(gene)))
                continue

            # Check if gene is already in the dictionary
            # Skip if it is already present to avoid unnecessary API calls
            if gene.lower() in self.aliases:
                continue

            # Start a timer to measure the time taken for the API request
            start_time = time.perf_counter()
            # Try searching by symbol
            data = fetch_hgnc(gene, field='symbol')
            # Handles request error
            if data is None:
                continue
            # Sleep to avoid hitting rate limit
            time.sleep(self._API_REQUEST_RATE)

            # If not found, try searching by alias
            if data['numFound']==0:
                # Restart the timer to avoid measuring elapsed time for two requests
                start_time = time.perf_counter()
                data = fetch_hgnc(gene, field='alias_symbol')
                # Handles request error
                if data is None:
                    continue
                # Sleep to avoid hitting rate limit
                time.sleep(self._API_REQUEST_RATE)
            
            # If found, add to dictionary
            if data['numFound'] > 0:
                symbol = data['docs'][0]['symbol']
                try:
                    alias_symbol = data['docs'][0]['alias_symbol']
                    
                    # Add each alias as key and gene as value
                    for alias in alias_symbol:
                        self.aliases[alias.lower()] = gene
                except KeyError:
                    pass

                # Add the symbol as key and gene as value
                self.aliases[symbol.lower()] = gene
                
            else:
                print('Gene not found: {}'.format(gene))
            
            # Add the gene itself as key and value
            self.aliases[gene.lower()] = gene

            # Adjust API request rate to target 10 requests per second
            elapsed_time += time.perf_counter() - start_time
            if idx >= 10:
                # Automatically adjust request rate based on average elapsed time of last n requests
                self._API_REQUEST_RATE += (0.1 - elapsed_time/idx)
                idx = 1
            else:
                idx += 1



    def save(self, path:str) -> None:
        '''
        Saves the alias dictionary to a JSON file.

        
        Parameters
        ----------
        path : str
            The file path where the alias dictionary will be saved. Directories on the path will be created if they do not already exist.
            A '.json' extension will be added to the path if not provided (example: 'path/to/file' --> 'path/to/file.json').
    
            
        Raises
        ------
        TypeError
            If the path is not a string.
        '''
        # Check that path is a string
        if not isinstance(path, str):
            raise TypeError('path must be a str')
        # Check that directory exists or create it
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        # Check for .json extension or add
        if not path.endswith('.json'):
            path += '.json'
        # Save alias dictionary to file
        with open(path, 'w') as f:
            json.dump(self.aliases, f, sort_keys=True)

    def load(self, path:str) -> None:
        '''
        Loads the alias dictionary from a JSON file.

        Parameters
        ----------
        path : str
            The path to the JSON file from which to load the alias dictionary.
        
            
        Raises
        ------
        TypeError
            If the path is not a string.
        FileNotFoundError
            If the file is not found or is not a JSON.
        '''
        # Check that path is a string
        if not isinstance(path, str):
            raise TypeError('path must be a str')
        # Check that file exists
        if not os.path.isfile(path):
            raise FileNotFoundError('File not found: ' + path)
        # Check for .json extension to make sure file type is correct
        if not path.endswith('.json'):
            raise FileNotFoundError('File must be JSON')
        # Load alias dictionary from file
        with open(path, 'r') as f:
            self.aliases = json.load(f)


