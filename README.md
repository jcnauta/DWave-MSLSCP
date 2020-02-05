# DWave-MSLSCP

Repository containing the generated problem files for the Multi-Service Location Set Covering Problem (MSLSCP) and their exact solutions.
Problems are named according to the parameters used to generate them;

F = number of services
L = number of locations
U = number of demand points

Each service, location and demand point is identified by an integer within its category (there can be a service and a location that both have number 0).
Connectivity of demand points to locations, as well as their demanded services are expressed in the form of triplets (the first three columns).
For example, the triplet (0, 4, 31) means that demand point 31 requests service 0, and could be serviced by location 4 (but there may be other suitable locations).

Additionally, locations have opening costs associated with them, to make them suitable for equipping services. These are listed in column D, corresponding to the locations in increasing row number (the first opening cost corresponds to location 0). The same goes for the equipping costs in column E; to equip a service on an opened location, the corresponding cost must be paid.