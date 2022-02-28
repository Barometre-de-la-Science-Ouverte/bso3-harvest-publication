oa_harvesting_strategy = [
    # arXiv
    lambda oa_location: 'repository_normalized' in oa_location and oa_location['repository_normalized'] == "arXiv",
    # PubMed Central
    lambda oa_location: 'repository_normalized' in oa_location and oa_location['repository_normalized'] == "PubMed Central",
    # HAL
    lambda oa_location: 'repository_normalized' in oa_location and oa_location['repository_normalized'] == "HAL",
    # repo
    lambda oa_location: 'repository_normalized' in oa_location and oa_location['host_type'] == "repository",
    # Wiley
    lambda oa_location: 'wiley' in oa_location['url_for_pdf'],
    # Else
    lambda oa_location: True
]