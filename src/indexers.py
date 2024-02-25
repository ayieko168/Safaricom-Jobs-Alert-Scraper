
import requests
import json
import hashlib

class APIIndexer:
    
    def __init__(self, url=None) -> None:
        
        if url:
            self.primary_url = url
        else:
            self.primary_url = "https://egjd.fa.us6.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations,flexFieldsFacet.values&finder=findReqs;siteNumber=CX,facetsList=LOCATIONS%3BWORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS,limit=50,sortBy=POSTING_DATES_DESC"
        
    def get_jobs(self) -> dict:
        return_dict = {}
        
        response = requests.get(self.primary_url)
        
        # Check if the response is successful
        if response.status_code != 200:
            return_dict['status'] = 'error'
            return_dict['message'] = 'Error fetching jobs'
            return_dict['data'] = None
            return return_dict
        
        # Parse the JSON response and return the jobs list
        response_json = response.json()
        jobs_list = response_json['items'][0]['requisitionList']
        
        parsed_jobs_list = []
        for job in jobs_list:
            
            job_description = {
                'job_hash': hashlib.md5(f"{job['Id']} {job['Title']} {job['PostedDate']}".encode('utf-8')).hexdigest(),
                'job_id': job['Id'],
                'job_title': job['Title'],
                'job_post_date': job['PostedDate'],
                'job_short_description': job['ShortDescriptionStr'],
                'job_location': f"{str(job['PrimaryLocation']).title()} ({str(job['PrimaryLocationCountry']).upper()})",
                'job_link': f"https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/{job['Id']}",
            }
            
            parsed_jobs_list.append(job_description)
        
        return_dict['status'] = 'success'
        return_dict['message'] = 'Jobs fetched successfully'
        return_dict['data'] = parsed_jobs_list
        
        # print(json.dumps(return_dict, indent=2))
        
        
        return return_dict






if __name__ == "__main__":
    indexer = APIIndexer()
    response = indexer.get_jobs()
    print(json.dumps(response, indent=2))













