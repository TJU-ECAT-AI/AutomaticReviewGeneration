import requests
def fetch_crossref_data(doi):
    """
    Fetch data from Crossref API for a given DOI.
    """
    base_url = "https://api.crossref.org/works/"
    response = requests.get(base_url + doi)
    if response.status_code == 200:
        return response.json()
    else:
        return None
def format_ris(data):
    """
    Format the data from Crossref into RIS format.
    """
    ris_data = []
    ris_data.append("TY  - JOUR")
    ris_data.append(f"T1  - {data['message']['title'][0]}")
    ris_data.append(f"AU  - {', '.join(author['family'] for author in data['message']['author'])}")
    ris_data.append(f"DO  - {data['message']['DOI']}")
    ris_data.append(f"PY  - {data['message']['created']['date-parts'][0][0]}")
    ris_data.append(f"JO  - {data['message']['container-title'][0]}")
    ris_data.append("ER  - ")
    return "\n".join(ris_data)
doi_list =[i for i in '''10.1038/s41467-020-18671-7
10.1038/s41467-020-18959-8
10.1038/s41467-020-19266-y
10.1038/s41467-021-23720-w
10.1038/s41467-021-22951-1
10.1038/s41467-023-39868-6
10.1038/s41467-023-43836-5
10.1038/s41565-021-00902-7
10.1038/s41597-022-01181-0
10.1038/s41597-023-02089-z
10.1038/s41597-022-01321-6
10.1038/s41524-020-0287-8
10.1021/acs.jpcc.1c10285
10.1038/s41929-022-00909-w
10.1038/s41467-018-07439-9'''.splitlines()]
for doi in doi_list:
    data = fetch_crossref_data(doi)
    if data:
        ris_formatted_data = format_ris(data)
        open(doi.replace('/','_')+'.ris' ,'w',encoding='UTF8').write(ris_formatted_data)
        print(f"RIS data for DOI {doi}")
    else:
        print(f"Failed to fetch data for DOI {doi}")
