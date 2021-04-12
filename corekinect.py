import requests
from typing import Any, List, Dict
import logging

logging.basicConfig(format='%(message)s', level=logging.DEBUG)
base = "https://api.corekinect.cloud:3000"


''' print_version
    Returns the version of CoreKinect being used 
'''
def print_version():
    version = requests.get(base + '/account/GetVersion')
    if not version:
        logging.error("No json data received in print_version()")
    logging.info('Requesting version...')
    logging.info('Status code: {}'.format(version.status_code))
    logging.info('Version: {}'.format(version.json()['Version']))


''' get_token
    Returns an access token 
'''
def get_token(client_id: str, client_secret: str) -> str:
    logging.info('Requesting token...')
    auth_params = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'content-type': 'application/x-www-form-urlencoded'
    }
    authorize = requests.get(url=base + '/auth/RequestToken',
                             params=auth_params,
                             auth=('user', 'pass'))
    if not authorize.json():
        logging.error("No json data received in get_token()")
    if "access_token" not in authorize.json():
        logging.error("No token received")
    logging.info('Status code: {}'.format(authorize.status_code))
    logging.info('Token: {}'.format(authorize.json()["access_token"]))
    return authorize.json()["access_token"]


# Id's are 16 character strings
# Activation codes are 32 character strings
''' add_devices
    Returns a list of Devices that could not be added 
'''
def add_devices(new_ids: List[str], new_acs: List[str], token: str) -> List[str]:
    logging.info('Adding devices...')
    dev_code_pairs = {
        "Authorization": 'Bearer {}'.format(token),
        "devices": [{"DeviceId": new_ids[i], "ActivationCode": new_acs[i]} for i in range(len(new_ids))]
    }
    attempt_add = requests.post(base + '/account/AddDevices', params=dev_code_pairs)
    if not attempt_add.json():
        logging.error("No json data received in add_devices()")
    if "DevicesPassed" not in attempt_add.json():
        logging.error("Failed to add any devices")
    passed = [id_dict["DeviceId"] for id_dict in attempt_add.json()["DevicesPassed"]]
    logging.info("Added successfully: {}".format(passed))
    return passed


''' create_endpoint
    Returns a dictionary containing the ID and URL of the new endpoint 
'''
def create_endpoint(token: str, devv_url: str) -> Dict[str, str]:
    logging.info('Creating endpoint...')
    endpoint = requests.post(base + '/account/CreateEndpoint', params={
        "URL": devv_url,
        "Authorization": 'Bearer {}'.format(token)
    })

    if not endpoint.json():
        logging.error("No json data received in create_endpoint()")
    if "EndpointId" not in endpoint.json():
        logging.error("EndpointId is missing from json response in create_endpoint()")
    logging.info('Endpoint ID: {}'.format(endpoint.json()["EndpointId"]))
    return endpoint.json()


#This feature is in Beta. Only supports the "client_credentials" grant type
''' create_oauth_endpoint
    Returns a dictionary containg the ID and URL of the new endpoint
'''
def create_oauth_endpoint(devv_url: str, auth_url: str, token: str,
                          AuthTokenType: str = "Bearer", AuthTokenKey: str = "access_token") -> Dict[str, str]:
    logging.info('Creating endpoint...')
    endpoint = requests.post(base + '/account/CreateEndpoint', params={
        "URL": devv_url,
        "AuthUrl": auth_url,
        "Authorization": 'Bearer {}'.format(token),
        "AuthTokenType": AuthTokenType,
        "AuthTokenKey": AuthTokenKey,
    })
    if not endpoint.json():
        logging.error("No json data received in create_endpoint()")
    if "EndpointId" not in endpoint.json():
        if "EndpointError" in endpoint.json():
            logging.error("Failed to get a token from AuthUrl with given parameters, response from AuthUrl was 400")
        else:
            logging.error("EndpointId is missing from json response in create_oauth_endpoint()")
    logging.info('Endpoint ID: {}'.format(endpoint.json()["EndpointId"]))
    return endpoint.json()


''' assign_to_endpoint
    Returns a list of Devices that could not be assigned 
'''
def assign_to_endpoint(device_ids: List[str], endpoint_id: str, token: str) -> List[str]:
    logging.info('Assigning devices to endpoint (ID: {})...'.format(endpoint_id))
    dev_params = {'EndpointId': endpoint_id, 'Devices': [{"DeviceId": device_id} for device_id in device_ids]}
    assign_device = requests.post(base + '/account/AssignDevicesToEndpoint',
                                  headers={'Authorization': 'Bearer {}'.format(token)},
                                  params=dev_params)

    if not assign_device.json():
        logging.error("No json data received in assign_to_endpoint()")
    if "DevicePassed" not in assign_device.json():
        logging.error("Failed to assign devices to endpoint")
    passed = [id_dict["DeviceId"] for id_dict in assign_device.json()["DevicePassed"]]
    logging.info('Successfully added: {}'.format(passed))
    return passed


''' delete_from_endpoint
    Returns a list of the given devices that were not associated with the given endpoint 
'''
def delete_from_endpoint(device_ids: List[str], endpoint_id: str, token: str) -> List[str]:
    print('Deleting devices from endpoint (ID: ' + endpoint_id + ')...')
    dev_params = {'EndpointId': endpoint_id, 'Devices': [{"DeviceId": device_id} for device_id in device_ids]}
    delete_device = requests.delete(base + '/account/DeleteDevicesFromEndpoint',
                                    headers={'Authorization': 'Bearer {}'.format(token)},
                                    params=dev_params)
    if not delete_device.json():
        logging.error("No json data received in delete_from_endpoint()")
    if "DevicePassed" not in delete_device.json():
        logging.error("Failed to delete (devices not found)")
    passed = [id_dict["DeviceId"] for id_dict in delete_device.json()["DevicePassed"]]
    logging.info("Deleted: {}".format(passed))
    return passed


''' delete_endpoints
    Returns a list of the given endpoints that did not exist or were not found 
'''
def delete_endpoints(kill_points: List[str], token: str) -> List[str]:
    logging.info('Deleting endpoints...')
    to_delete = {
        "Endpoints": [{"EndpointId": endpoint} for endpoint in kill_points]
    }
    deleted_endpoints = requests.delete(base + '/account/DeleteEndpoints',
                                        headers={'Authorization': 'Bearer ' + token},
                                        params=to_delete)
    if not deleted_endpoints.json():
        logging.error("No json data received in delete_endpoints()")
    if "EndpointsDeleted" not in deleted_endpoints.json():
        logging.error("Endpoints not found")
    deleted = [point_dict["EndpointId"] for point_dict in deleted_endpoints.json()["EndpointsDeleted"]]
    logging.info("Deleted endpoints: {}".format(deleted))
    return deleted


''' get_endpoints
    Returns a list of endpoints as dictionary elements containing keys 
        "EndpointId", "URL", "DataType" 
'''
def get_endpoints(token: str) -> List[Dict[str, str]]:
    logging.info('Requesting list of endpoints...')
    endpoints = requests.get(base + '/account/GetEndpoints/',
                             headers={'Authorization': 'Bearer {}'.format(token)})

    if not endpoints.json():
        logging.error("No json data received in get_endpoints()")
    if "EndpointId" not in endpoints.json():
        logging.error("Endpoints are missing from json response in get_endpoints()")
    for entry in endpoints.json()["Endpoints"]:
        logging.info('Found: {}'.format(entry.values()))
    return endpoints.json()["Endpoints"]


''' get_devices
    Returns a list of devices as dictionary elements with keys 
        "DeviceId", "DeviceType", "Endpoints" 
'''
def get_devices(token: str) -> List[Dict[str, Any]]:
    logging.info('Requesting list of devices...')
    devices = requests.get(base + '/account/GetDevices/',
                           headers={'Authorization': 'Bearer {}'.format(token)})
    if not devices:
        logging.error("No json data received in get_devices()")
    if "Devices" not in devices:
        logging.error("No devices found")
    found = [entry["DeviceId"] for entry in devices["Devices"]]
    logging.info("Found devices: {}".format(found))
    return devices.json()["Devices"]


''' get_devices_by_location
    Returns a list of locations as dictionary elements with keys
        "LocationName", "DeviceType", "Devices" 
'''
def get_devices_by_location(token: str) -> List[Dict[str, Any]]:
    logging.info('Requesting device list by location...')
    devices = requests.get(base + '/account/GetDevicesByLocation/',
                           headers={'Authorization': 'Bearer {}'.format(token)})

    if not devices:
        logging.error("No json data received in get_devices_by_location()")
    if "Devices" not in devices:
        logging.error("No devices found")
    logging.info("Locations found: {}".format([entry["LocationName"] for entry in devices]))
    return devices.json()


''' get_locations
    Returns a list of locations as dictionary elements with keys:
        "LocationName", "Lattitude", "Longitude" 
'''
def get_locations(token: str) -> List[Dict[str, Any]]:
    logging.info('Requesting location list...')
    locations = requests.get(base + '/account/GetLocations/',
                             headers={'Authorization': 'Bearer {}'.format(token)})

    if not locations:
        logging.error("No json data received in get_locations()")
    logging.info("Locations found: {}".format([entry["LocationName"] for entry in locations]))
    return locations.json()


''' get_location_reports
    Returns a list of locations as dictionary elements with the following keys:  
        "DeviceTypeName",
        "LocationName",
        "ReportGenerated",
        "DeviceCount",
        "TotalCheckedIn",
        "TotalCheckedInWithin24",
        "Stats" {
            "AccuracyByCategory" {"Count", "RangeMin", "RangeMax"},
            "AccuracyOverall"
        }           
'''
def get_location_reports(token: str) -> List[Dict[str, Any]]:
    logging.info('Requesting location reports...')
    reports = requests.get(base + '/account/GetLocationReports',
                           headers={'Authorization': 'Bearer {}'.format(token)})
    if not reports:
        logging.error("No json data received in get_location_reports")
    logging.info("Reports generated for: {}".format([entry["LocationName"] for entry in reports]))
    return reports.json()

if __name__ == '__main__':
    print_version()
