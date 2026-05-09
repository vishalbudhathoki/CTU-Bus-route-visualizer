import json, re

with open("data.json", "r", encoding="utf-8") as f:
    raw = json.load(f)
stations = json.loads(raw["data"])
by_id = {s["stationid"]: s for s in stations}

# Build name lookup (lowercase -> station)
by_name = {}
for s in stations:
    by_name[s["stationname"].lower().strip()] = s

def find(name):
    n = name.lower().strip()
    if n in by_name:
        return by_name[n]["stationid"]
    for k, v in by_name.items():
        if n in k or k in n:
            return v["stationid"]
    return None

# Route definitions: [route_id, name, description, color, stop_ids, time_range, frequency, length_km, num_buses]
routes_raw = [
    {
        "id": "1", "name": "New Maloya Colony to Manimajra",
        "desc": "Via Dadumajra village, CTU W/S, 25/38, 24/25, PGI, 15Mkt, 16Mkt, 17/16, ISBT-17, 18Mkt, 19Mkt, 27Mkt, 28 Mkt, CTU W/shop, R/Stn, R/Crossing, Kalagram, H/B Chowk",
        "color": "#E91E63",
        "stops": [259, 171, 137, 175, 577, 290, 191, 148, 373, 112, 60, 21, 114, 121, 126, 134, 39, 51, 416, 145, 620, 414],
        "time": "06:10-18:40", "freq": "20 min", "length": 24, "buses": 8
    },
    {
        "id": "2A", "name": "Manimajra to Manimajra",
        "desc": "Via Indira Colony, M/Complex, R/Crossing, Sec-28/26 G.Mkt, 19/7, 18/8, 22/17, 16/10, 15/11, PGI, Khuda Lahora, S/P Barrier, Dhanas, DMC, CTU Workshop, 25/38, 25/24, 24/15, 23/16, ISBT-17, 18/21, 19/20, 27/30, 28/29, Elante Mall, Colony No.4, CTU Workshop, R/Station, R/Crossing, H.B.Chowk",
        "color": "#4CAF50",
        "stops": [414, 536, 150, 416, 250, 90, 86, 552, 54, 119, 148, 70, 72, 101, 577, 39, 290, 191, 297, 333, 21, 325, 326, 327, 328, 96, 91, 39, 51, 416, 620],
        "time": "05:40-20:30", "freq": "20-25 min", "length": 38.3, "buses": 6
    },
    {
        "id": "2C", "name": "Manimajra to Manimajra",
        "desc": "Via H.B.Chowk, R/Station, CTU W/Shop, Colony No-4, Elante Mall, Sec-29/28, 30/27, 20/19, 21/18, 22/17, 16/23, 15/24, 24/25, 38/25, CTU W/Shop, DMC, Dhanas, SP Barrier, K.Lahora, PGI, 11/15, 10/16, ISBT-17, 8/18, 7/19, 26/28, G.Mkt, R/Crossing, M/Complex, M.M.Town, Indra Colony",
        "color": "#2196F3",
        "stops": [620, 51, 39, 91, 96, 329, 330, 331, 332, 552, 333, 296, 190, 290, 577, 101, 72, 70, 148, 118, 54, 21, 86, 89, 128, 250, 416, 150, 374, 536],
        "time": "05:30-20:20", "freq": "20-25 min", "length": 38.3, "buses": 6
    },
    {
        "id": "4A", "name": "ISBT-43 to ISBT-43",
        "desc": "Via 43/44, 35/34, Aroma, 22/17, 16/17, R/Garden, 16/10 Hospital, OPD, PGI, K/Lahora, IRB, S/P Barrier, Dhanas, DMC, CTU Depot-III, 38west, Maloya, Ph-6, Old Barrier, Franco, Badheri Chowk, 40/41, 41mkt, 42mkt",
        "color": "#FF9800",
        "stops": [22, 83, 573, 48, 552, 59, 604, 54, 534, 148, 70, 357, 72, 101, 577, 174, 171, 170, 169, 168, 276, 209, 125, 32],
        "time": "06:45-16:50", "freq": "25-30 min", "length": 32.5, "buses": 4
    },
    {
        "id": "4C", "name": "ISBT-43 to ISBT-43",
        "desc": "Via 43/44, 42mkt, 41mkt, 41/40, Badheri Chowk, Franco, O/Barrier, Ph-6, Maloya, 38west, CTU Depot-III, DMC, Dhanas, S/P Barrier, K/Lahora, PGI, OPD, 10/11, 10/16, 17/16, ISBT-17, Aroma, 34/35, 44/43",
        "color": "#9C27B0",
        "stops": [22, 83, 32, 125, 413, 276, 168, 169, 170, 171, 174, 577, 101, 72, 70, 148, 534, 611, 54, 60, 21, 48, 938, 84],
        "time": "07:00-17:05", "freq": "25-30 min", "length": 32.5, "buses": 4
    },
    {
        "id": "5A", "name": "Ram Darbar to Ram Darbar",
        "desc": "Via Sec-47, 46/47, 32/31, 30/29, 27/28, 27/26, 19/7, 18/8, 17/9, 16/10, 15/11, PGI, Uni, 15/14, 24/25, 37/38, 38/40, 39/38west, Maloya, 39, 40, 41, 42 mkts, ISBT-43, 44, 45, 46, 47 mkts, Ram Darbar",
        "color": "#F44336",
        "stops": [94, 153, 180, 181, 183, 185, 79, 90, 86, 173, 54, 119, 148, 188, 190, 38, 192, 194, 171, 632, 200, 125, 32, 22, 201, 203, 204, 153, 94],
        "time": "05:45-21:25", "freq": "10 min", "length": 38.4, "buses": 12
    },
    {
        "id": "5C", "name": "Ram Darbar to Ram Darbar",
        "desc": "Via Sec-47 mkt, 46, 45, 44 mkts, ISBT-43, 42, 41, 40, 39 mkts, Maloya, 38W/39, 38/40, 38/37, 25/24, 14/15, Uni, PGI, 11/15, 10/16, 9/17, 8/18, 7/19, 26/27, 28/27, 29/30, 31/32, 47/46, 47 mkt",
        "color": "#00BCD4",
        "stops": [94, 153, 204, 203, 201, 22, 32, 125, 200, 632, 171, 194, 192, 37, 191, 189, 148, 118, 54, 173, 86, 89, 80, 186, 184, 181, 182, 153],
        "time": "05:40-19:30", "freq": "10 min", "length": 38.4, "buses": 12
    },
    {
        "id": "6", "name": "New Maloya Colony to Raipur Kalan",
        "desc": "Via Maloya, 38west, 38Mkt, 37Mkt, 36/37, 41/42, Sec-42, ISBT-43, 43/44, 35/34, 34 Mkt, 33 Mkt, 32 Mkt, 31 Mkt, Ramdarbar, Tribune Chowk, Hallo Majra, Vikas Nagar",
        "color": "#795548",
        "stops": [259, 171, 174, 360, 33, 286, 31, 32, 22, 83, 573, 362, 363, 365, 16, 94, 12, 9, 381],
        "time": "05:50-18:35", "freq": "30 min", "length": 25.5, "buses": 6
    },
    {
        "id": "7", "name": "New Maloya Colony to Ramdarbar",
        "desc": "Via Maloya, 38West LP, 25/38, 25/24, 24 Mkt, 23 Mkt, 23/22, ISBT-17, Aroma, 21 Mkt, 20 Mkt, 30 Mkt, 29/30, GMCH-32, 31/32, SD-College, 46/47, 47 Mkt, Industrial Area Phase-2",
        "color": "#607D8B",
        "stops": [259, 171, 174, 290, 191, 370, 369, 61, 21, 48, 66, 69, 135, 184, 17, 181, 696, 180, 153, 571],
        "time": "06:45-18:20", "freq": "25 min", "length": 21.5, "buses": 6
    },
    {
        "id": "9A", "name": "Mansa Devi to Mansa Devi",
        "desc": "Via M/Majra, H.Board, R/Cross, R.Station, CTU W/Shop, 28/26 G/Mkt, 27/19, 30/20, 32/33, 46/45, 50/49, 64/63, 68/67, 67/80, Sec-66, Ph-11, 48/Jagatpura, 47 outer, R/Darbar, Ind.Area Ph-2, Tribune, 29, 28 P/Pump, CTU w/s, R/S, R/C, H.Board, M/Majra",
        "color": "#FF5722",
        "stops": [88, 414, 620, 51, 39, 250, 242, 330, 291, 284, 308, 225, 348, 430, 319, 320, 337, 155, 94, 571, 12, 131, 130, 39, 51, 620, 414],
        "time": "06:10-20:30", "freq": "30 min", "length": 37, "buses": 4
    },
    {
        "id": "9C", "name": "Mansa Devi to Mansa Devi",
        "desc": "Via M.majra, H.B Chowk, R.Crossing, R.Station, CTU W/Shop 28 P.Pump, Ind.Area/29, Tribune, Ind.Area Ph-2, Ramdarbar, Outer47, Jagatpura, Ph-11, Sec-66, 80/67, 68/67, 63/64, 50/49, 45/46, 33/32, 20/30, 19/27, 26/27, G/Mkt-26, TPT/C, R.Crossing, HBC, Manimajra",
        "color": "#3F51B5",
        "stops": [88, 414, 620, 416, 51, 39, 130, 136, 12, 571, 94, 155, 349, 320, 319, 430, 348, 225, 308, 285, 289, 330, 242, 80, 250, 458, 416, 620, 414],
        "time": "05:40-20:45", "freq": "30 min", "length": 37, "buses": 4
    },
    {
        "id": "10", "name": "ISBT-43 to Manimajra",
        "desc": "Via Sec-44/51, 45 Mkt, 46 Mkt, 47 mkts, Ram Darbar, Tribune Chowk, Poultry Farm, Colony No.4, CTU w/s, R/Station, Railway Crossing, H/B Chowk",
        "color": "#009688",
        "stops": [22, 344, 203, 204, 153, 94, 12, 339, 91, 39, 51, 416, 620, 414],
        "time": "05:25-20:35", "freq": "20 min", "length": 17.5, "buses": 7
    },
    {
        "id": "11", "name": "Railway Station to Civil Sectt.",
        "desc": "Via CTU W/shop, Sec-26 G/Mkt, 26/27, 7/19, 8/18, ISBT-17, UT Sectt., High Court",
        "color": "#8BC34A",
        "stops": [51, 39, 250, 80, 89, 86, 21, 176, 20],
        "time": "08:35-16:40", "freq": "60 min", "length": 15, "buses": 2
    },
    {
        "id": "11A", "name": "Rock Garden to Sukhna Lake",
        "desc": "Via Bird Park",
        "color": "#CDDC39",
        "stops": [615, 672, 256],
        "time": "10:10-15:50", "freq": "30 min", "length": 3, "buses": 1
    },
    {
        "id": "14", "name": "ISBT-43 to Mansa Devi",
        "desc": "Via 43/44, 35/34, 23/22, ISBT-17, 8/9, Lake Chowk, Kishangarh, IT Park, Mansa Devi Complex",
        "color": "#E040FB",
        "stops": [22, 83, 573, 61, 21, 281, 680, 143, 149, 685, 88],
        "time": "08:30-14:30", "freq": "60 min", "length": 17, "buses": 2
    },
    {
        "id": "17", "name": "ISBT-43 to Behlana",
        "desc": "Via 42/43, 36/35, 23/22, ISBT-17, Aroma, 21 Mkt, 20 Mkt, 30 Mkt, 29 Mkts, Elante Mall, Colony No.4, H/Majra, Behlana",
        "color": "#FF6F00",
        "stops": [22, 65, 62, 61, 21, 48, 66, 69, 135, 131, 96, 91, 9, 7],
        "time": "05:35-19:00", "freq": "15 min", "length": 15.5, "buses": 8
    },
    {
        "id": "18", "name": "ISBT-43 to Kaimbwala",
        "desc": "Via 42/43, Attawa, 36/35, 23/22, 17 B/S, 17/18, 9/8, 9 mkt, MLA Flat, Pb.Civil.Sectt, H/Court, Lake, Kaimbwala",
        "color": "#1B5E20",
        "stops": [22, 65, 206, 62, 61, 21, 81, 280, 428, 2, 36, 20, 256, 152, 151],
        "time": "06:10-20:15", "freq": "30 min", "length": 15.5, "buses": 4
    },
    {
        "id": "20", "name": "Chandigarh to Kharar",
        "desc": "Via Aroma, Sec-21 Mkt, 20/21, 33/34, 44/45, ISBT-43, YPS, Ph-7, Sohana, Lakhnaur, Landran, Chappar Chiri, Sante Majra",
        "color": "#880E4F",
        "stops": [48, 66, 459, 392, 282, 22, 98, 312, 97, 271, 123, 274, 275, 24],
        "time": "05:30-20:45", "freq": "15-30 min", "length": 25.6, "buses": 9
    },
    {
        "id": "22", "name": "ISBT-43 to IT Park",
        "desc": "Via 42/43, 36/35, 23/22, ISBT-17, 17/18 L/Point, 18, 19, 27, 28 mkts, CTU w/s, R/Station, R/Crossing, H/B Chowk, M/Majra, Kishangarh",
        "color": "#0D47A1",
        "stops": [22, 65, 62, 61, 21, 81, 114, 121, 126, 134, 39, 51, 416, 620, 414, 143, 149],
        "time": "05:40-20:30", "freq": "20 min", "length": 19.6, "buses": 7
    },
    {
        "id": "23A", "name": "ISBT-43 to Khuda Ali Sher",
        "desc": "Via 43/44, 35/34, Aroma, 22/17, 16/17, 16/10, 15/11, PGI, New OPD, PEC, Naya Gaon",
        "color": "#00695C",
        "stops": [22, 83, 573, 48, 552, 59, 54, 119, 148, 146, 49, 261, 338],
        "time": "05:30-21:30", "freq": "15 min", "length": 12.8, "buses": 8
    },
    {
        "id": "26", "name": "Mullanpur Eco City to Dhakoli",
        "desc": "Via Mullanpur, S.P.Barrier, K.Lahora, PGI, OPD, 2/11, 10/11, 10/16, ISBT-17, 19/20, 28 P.P., CTU w/s, R/S, Colony No.4, Hallo Majra, Airport, Zirakpur, Dhakoli",
        "color": "#33691E",
        "stops": [624, 154, 72, 70, 148, 146, 995, 611, 54, 21, 326, 130, 39, 51, 91, 9, 161, 45, 340],
        "time": "06:00-19:25", "freq": "35 min", "length": 32, "buses": 6
    },
    {
        "id": "28", "name": "New Maloya Colony to Manimajra",
        "desc": "Via Maloya, Daddu Majra Village, 38w, 38Mkt, 37Mkt, 36Mkt, 36/35, 23/22, ISBT-17, 8/18, 7/19, 26/28, 26-G/Mkt, CTU w/s, R/Station, Kalagram, H.Board",
        "color": "#BF360C",
        "stops": [259, 171, 137, 174, 360, 33, 372, 62, 61, 21, 86, 89, 128, 250, 39, 51, 145, 620],
        "time": "06:15-20:00", "freq": "30 min", "length": 26, "buses": 6
    },
    {
        "id": "28A", "name": "ISBT-43 to Rani Majra",
        "desc": "Via 43/44, 35/34, 23/22, ISBT-17, 17/9 KC, 16/10, 11/15, PGI, Khuda Lahora, S.P.Barrier, Mullanpur, ECO-City, DLF Chowk, Todde Majra, Rasulpur, Omax Phase-II",
        "color": "#AD1457",
        "stops": [22, 83, 573, 61, 21, 173, 54, 118, 148, 70, 72, 154, 624, 689, 690, 691, 692],
        "time": "07:10-19:15", "freq": "75 min", "length": 23, "buses": 2
    },
    {
        "id": "28B", "name": "ISBT-43 to Eco City Block-2 (Takipur)",
        "desc": "Via 42/43, Attawa, 36/35, 37/24, 38/25, DMC, Dhanas, S/P Barrier, Mullanpur, Homi Bhaba, Parol, Majra, Hosiarpur, Eco City",
        "color": "#4A148C",
        "stops": [22, 65, 206, 62, 197, 290, 577, 101, 72, 154, 668, 277, 279, 703, 624, 983],
        "time": "06:50-19:20", "freq": "25 min", "length": 23, "buses": 6
    },
    {
        "id": "30", "name": "ISBT-43 to Nada Sahib",
        "desc": "Via 42/43, Attawa, 36/35, 23/22, ISBT-17, Aroma, 21, 20 Mkts, 19 Mkt, 19/27, 26/27, G.Mkt-26, R/C, Kalagram, H.Board, Manimajra, Command Hospital, Majri Chowk",
        "color": "#1A237E",
        "stops": [22, 65, 206, 62, 61, 21, 48, 66, 69, 199, 80, 250, 416, 145, 620, 414, 92, 557, 120],
        "time": "06:05-19:55", "freq": "25-30 min", "length": 21.5, "buses": 6
    },
    {
        "id": "30A", "name": "ISBT-43 to Cantonment",
        "desc": "Via 42/43, Attawa, 36/35, K/Bhawan, 22/35, 21/34, 20/33, 30/32, 29/31, Tribune, H/Majra, Colony No.4, CTU w/s, R/Station, R/Crossing, Kalagram, H.B Chowk, Fun Republic, Command Hospital, Tank Chowk",
        "color": "#311B92",
        "stops": [22, 65, 206, 62, 678, 255, 253, 264, 249, 247, 12, 9, 91, 39, 51, 416, 145, 620, 425, 92, 266, 25],
        "time": "05:10-20:45", "freq": "30 min", "length": 21.1, "buses": 5
    },
    {
        "id": "30B", "name": "ISBT-43 to Ramgarh",
        "desc": "Via 42/43, Attawa, 36/35, 23/22, ISBT-17, Aroma, 21 Mkt, 20 Mkts, 19/27, 27 Mkt, G.Mkt-26, R/C, Kalagram, H.Board, 11/15 Pkl, 12/11 Pkl, Rally Chowk, Sec-4 Pkl, Nada Sahib",
        "color": "#827717",
        "stops": [22, 65, 206, 62, 61, 21, 48, 66, 69, 199, 126, 250, 416, 145, 620, 267, 116, 300, 120, 406],
        "time": "06:30-19:00", "freq": "25 min", "length": 31, "buses": 8
    },
    {
        "id": "32", "name": "PGI to Derabassi",
        "desc": "Via OPD, Sec-11/10, 10/16, 17/16, ISBT-17, 8/18, 7/19, 26/28, G.Mkt-26, R/C, H/B, M/Majra, Old Pkl, Nada Sahib, Ramgarh, Mubarakpur",
        "color": "#E65100",
        "stops": [148, 534, 611, 54, 60, 21, 86, 89, 128, 250, 416, 620, 414, 34, 120, 406, 270, 23],
        "time": "05:00-20:55", "freq": "15-30 min", "length": 37.7, "buses": 14
    },
    {
        "id": "34", "name": "PGI to Derabassi",
        "desc": "Via OPD, PEC, 10/16, ISBT-17, Aroma, Piccadilly Chowk, 21/34, 20/33, 30/32, 29/31, Hallo Majra, Airport, Zirakpur, Bhankarpur, Mubarakpur",
        "color": "#F57F17",
        "stops": [148, 534, 49, 54, 21, 48, 581, 253, 264, 249, 247, 9, 161, 45, 140, 270, 23],
        "time": "06:15-19:25", "freq": "20 min", "length": 28, "buses": 9
    },
    {
        "id": "35", "name": "ISBT-17 to Kharar",
        "desc": "Via Aroma, 35/22, Kissan Bhawan, 35/36, Attawa, 36/37, 40/41, F/Chowk, Ph-2, Ph-6, Balongi, Daun, Desu Majra, Mundi Kharar",
        "color": "#006064",
        "stops": [21, 48, 254, 580, 63, 206, 286, 209, 276, 170, 141, 162, 166, 24],
        "time": "05:40-22:20", "freq": "20 min", "length": 18.3, "buses": 5
    },
    {
        "id": "35B", "name": "ISBT-17 to Kharar",
        "desc": "Via Aroma, 35/22, Kissan Bhawan, 35/36, Attawa, ISBT-43, F/Chowk, Ph-2, Ph-6, Balongi, Daun, Desu Majra, Mundi Kharar",
        "color": "#004D40",
        "stops": [21, 48, 254, 580, 63, 206, 22, 276, 170, 141, 162, 166, 24],
        "time": "05:20-22:00", "freq": "10-20 min", "length": 19.2, "buses": 9
    },
    {
        "id": "39", "name": "Mohali Ph-11 to PGI",
        "desc": "Via Mohali Rly Stn, Ind.Area Ph-9, Sec-66/67, 67/68, 68 outer, 69/68, Kumbra, Fortis, Ph-7, Chawla Chowk, 60/61, 52/61, YPS, ISBT-43, 42/43, 36/35, 23/22, ISBT-17, 22/17, 16/10, 11/10, PEC, OPD",
        "color": "#263238",
        "stops": [320, 355, 354, 319, 226, 245, 314, 312, 311, 212, 99, 98, 22, 65, 62, 61, 21, 552, 54, 611, 49, 534, 148],
        "time": "05:50-21:20", "freq": "15 min", "length": 27.5, "buses": 12
    },
    {
        "id": "71", "name": "ISBT-43 to Saketri (Kaimbwala)",
        "desc": "Via 43/44, 35/34, K.Bhawan, 23/22, ISBT-17, 18, 19, 27 Mkts, G/Mkt, R/Crossing, M/M Complex, M/M Town, M/Majra, Swastik Vihar, Mansa Devi, Saketri",
        "color": "#546E7A",
        "stops": [22, 83, 573, 580, 61, 21, 114, 121, 126, 250, 416, 150, 374, 414, 88, 334],
        "time": "07:30-19:30", "freq": "30 min", "length": 24, "buses": 6
    },
    {
        "id": "79", "name": "PGI to Chhattbir Zoo",
        "desc": "Via OPD, PEC, 10/16, ISBT-17, Aroma, 21, 20 Mkt, 20/30, 32 Hospital, Tribune Chowk, Hallo Majra, Airport, Zirakpur, Dayalpura",
        "color": "#37474F",
        "stops": [148, 534, 49, 54, 21, 48, 66, 69, 330, 249, 12, 9, 161, 45, 385, 387],
        "time": "07:00-18:15", "freq": "45 min", "length": 27.9, "buses": 4
    },
    {
        "id": "80", "name": "PGI to Zirakpur",
        "desc": "Via New OPD, PEC, 10/16, ISBT-17, Aroma, 20 mkt, 30 mkt, 29 mkt, Elante Mall, Colony No.4, Hallomajra, Mouli Jagran, Raipur Kalan, Baltana",
        "color": "#455A64",
        "stops": [148, 534, 49, 54, 21, 48, 69, 135, 131, 96, 91, 9, 263, 382, 383, 45],
        "time": "06:30-20:15", "freq": "30 min", "length": 20, "buses": 5
    },
    {
        "id": "85", "name": "ISBT-43 to Zirakpur",
        "desc": "Via 42/43, Attawa, Kissan Bhawan, 23/22, ISBT-17, Aroma, Piccadilly Chowk, 21/34, 20/33, 30/32, 29/31, Tribune Chowk, Hallomajra, Mouli Jagran, Raipur Kalan, Baltana",
        "color": "#78909C",
        "stops": [22, 65, 206, 580, 61, 21, 48, 581, 253, 264, 249, 247, 12, 9, 263, 382, 383, 45],
        "time": "06:15-19:45", "freq": "30 min", "length": 19.5, "buses": 5
    },
    {
        "id": "239", "name": "ISBT-43 to Lake",
        "desc": "Via 43/44, 35/34, Aroma, ISBT-17, 17/18, 9/8 K.C., UT Sectt., MLA Flat, H/Court, Bird Park",
        "color": "#0277BD",
        "stops": [22, 83, 573, 48, 21, 81, 280, 176, 2, 20, 672, 256],
        "time": "07:20-20:15", "freq": "20 min", "length": 14, "buses": 5
    },
    {
        "id": "551", "name": "ISBT-43 to PGI",
        "desc": "Via Sector 34/35, Aroma, Sector 22/17, 16 General Hospital, New OPD",
        "color": "#C62828",
        "stops": [22, 938, 48, 552, 54, 534, 148],
        "time": "05:30-20:20", "freq": "10 min", "length": 11, "buses": 9
    },
    {
        "id": "2F", "name": "PGI to Platinum Homes",
        "desc": "Via New OPD, 2/11, 10/16, 17/16, ISBT-17, 17/18, 8/18, 7/19, 26/27, 26/28 G.Mkt, TPT area, CTU w/s, Rly/Stn, Rly/Crossing, H.B.Chowk, Panchkula Sector-8/17, 9/16, 10/15, 11/12, Pkl B/S, Sec-4, 21, 20 Pkl, Sushma Square/Dhakoli, Platinum Homes",
        "color": "#D81B60",
        "stops": [148, 146, 995, 54, 60, 21, 81, 86, 89, 80, 128, 458, 39, 51, 416, 620, 476, 202, 224, 116, 324, 300, 322, 695, 981],
        "time": "05:40-18:50", "freq": "20-25 min", "length": 31, "buses": 10
    },
    {
        "id": "240", "name": "ISBT-43 to Mata Mansa Devi",
        "desc": "Via 43/44, 35/34, Kissan Bhawan, 23/22, ISBT-17, Aroma, 21, 20, 30, 29 mkts, Elante Mall, Colony No.4, CTU w/s, R/Station, R/Crossing, Kalagram, H/B Chowk, M/Majra",
        "color": "#6A1B9A",
        "stops": [22, 83, 573, 580, 61, 21, 48, 66, 69, 135, 131, 96, 91, 39, 51, 416, 145, 620, 414, 88],
        "time": "05:15-20:50", "freq": "30 min", "length": 20.4, "buses": 5
    },
    {
        "id": "202", "name": "ISBT-43 to Pb. Civil Sectt. (High Court)",
        "desc": "Via 43/44, 42/43, 36/35, 23/22, ISBT-17, 17/18, KC, UT Sectt, MLA Flat, H/Court, Pb/HR Sectt.",
        "color": "#1565C0",
        "stops": [22, 83, 65, 62, 61, 21, 81, 173, 176, 2, 20, 36],
        "time": "07:15-20:00", "freq": "15 min", "length": 13, "buses": 6
    },
    {
        "id": "206", "name": "ISBT-43 to IT Park",
        "desc": "Via Attawa, Kissan Bhawan, 23/22, ISBT-17, 17/18, 8/18, 7/19, 26/27, G/Mkt, TPT, R/Crossing, H/B Chowk, M/Majra, Indira Colony, Kishangarh",
        "color": "#283593",
        "stops": [22, 206, 580, 61, 21, 81, 86, 89, 80, 250, 458, 416, 620, 414, 536, 143, 149],
        "time": "06:10-19:20", "freq": "20 min", "length": 18.1, "buses": 7
    },
    {
        "id": "8", "name": "Mohali Ph-XI to PGI",
        "desc": "Via Sec-49/48, Jagatpura, 47 Mkt, 46 Mkt, 45 Mkt, 44 Mkt, ISBT-43, 44/43, 35/34, Aroma, 22/17, 16/17, 16/10 Hospital, PEC, OPD",
        "color": "#558B2F",
        "stops": [320, 337, 349, 153, 204, 203, 201, 22, 84, 573, 48, 552, 59, 54, 49, 534, 148],
        "time": "06:05-20:50", "freq": "75 min", "length": 21, "buses": 2
    },
    {
        "id": "2B", "name": "PGI to Mansa Devi",
        "desc": "Via N/OPD, 10/16, 18/17, 8/18, 7/19, 26/27, G/Mkt, CTU W/S, R/Station, H/B Chowk, M/Majra",
        "color": "#2E7D32",
        "stops": [148, 534, 54, 555, 86, 89, 80, 250, 39, 51, 620, 414, 88],
        "time": "06:00-20:00", "freq": "30 min", "length": 20, "buses": 4
    },
    {
        "id": "7C", "name": "ISBT-17 to ISBT-17",
        "desc": "Via Aroma, 21, 20, 30, 29 mkts, Tribune, Ind.Area Ph-II, Ram Darbar, 31, 32, 33, 34, 35 mkts, ISBT-43, 43/44, 42, 41/42, 36/37, 37, 38 mkts, 39/38west, Maloya, 38west, 25/38, 24, 23 mkts, 23/22",
        "color": "#1B5E20",
        "stops": [21, 48, 66, 69, 135, 131, 12, 571, 94, 16, 365, 363, 362, 573, 22, 83, 65, 31, 286, 33, 360, 194, 171, 174, 290, 370, 369, 61],
        "time": "05:40-19:30", "freq": "10 min", "length": 38, "buses": 12
    },
    {
        "id": "35A", "name": "ISBT-17 to Sector-123",
        "desc": "Via 16/17, 16/10, 11/15, PEC, New OPD, PGI, 14/15, 24/25, 37/38, 40/41, P.B.Barrier, Balongi, Daun, KFC, Jalvayu Tower, Sec-124/125",
        "color": "#00838F",
        "stops": [21, 59, 54, 119, 49, 146, 148, 189, 190, 38, 209, 141, 162, 663, 665, 664],
        "time": "06:00-20:40", "freq": "40 min", "length": 23, "buses": 4
    },
    {
        "id": "38AS", "name": "ISBT-17 to New Airport",
        "desc": "Via ISBT-43, Sohana, Sec-82, Mohali Airport Chowk",
        "color": "#BF360C",
        "stops": [21, 22, 97, 694, 161],
        "time": "01:50-23:30", "freq": "20-40 min", "length": 22, "buses": 8
    },
    {
        "id": "76", "name": "ISBT-17 to Kurali",
        "desc": "Via Mullanpur, Block",
        "color": "#4E342E",
        "stops": [21, 148, 70, 72, 154, 160, 561],
        "time": "05:15-20:15", "freq": "30-40 min", "length": 31, "buses": 4
    },
    {
        "id": "123A", "name": "PGI to Mohali R/Station Phase-11",
        "desc": "Via OPD, PEC, 11/10, 10/16, ISBT-17, Aroma, 34/35, 44/43, ISBT-43, 51 mkt, UT Border, 62/63, 63 mkt, 64 mkt, 65 mkt",
        "color": "#EF6C00",
        "stops": [148, 534, 49, 611, 54, 21, 48, 938, 84, 22, 260, 99, 346, 351, 353, 320, 355],
        "time": "06:25-19:40", "freq": "30 min", "length": 19.8, "buses": 5
    },
    {
        "id": "241", "name": "ISBT-43 to Mansa Devi",
        "desc": "Via 52/53, 52/61, YPS, 51 mkt, 51/50, 50 mkt, 49/50, 50/45, 44C Gaushala, 45 mkt, 45/46, 32/33, 20/30, 19/27, 27 mkt, G/Mkt-26, CTU w/s, Ind.Area Ph-1, R/Station, R/Crossing, H/B Chowk, M/Majra",
        "color": "#8E24AA",
        "stops": [22, 229, 99, 260, 237, 402, 359, 1023, 942, 203, 285, 291, 330, 199, 126, 250, 39, 956, 51, 416, 620, 414, 88],
        "time": "05:20-21:10", "freq": "20-25 min", "length": 24.5, "buses": 7
    },
    {
        "id": "212", "name": "PGI to Derabassi",
        "desc": "Via New OPD, PEC, 10/16, ISBT-17, Aroma, Piccadilly Chowk, 21/34, 20/33, 30/32, 29/31, Hallomajra, Airport, Zirakpur, Bhankarpur",
        "color": "#D84315",
        "stops": [148, 534, 49, 54, 21, 48, 581, 253, 264, 249, 247, 9, 161, 45, 140, 23],
        "time": "06:10-19:50", "freq": "20 min", "length": 26.5, "buses": 8
    },
    {
        "id": "216", "name": "ISBT-43 to Derabassi",
        "desc": "Via 42/43, Attawa, 36/35, Kissan Bhawan, 23/22, ISBT-17, Aroma, 21/34, 20/33, 30/32, Tribune Chowk, Hallo Majra, Airport Chowk, Zirakpur, Bhankarpur",
        "color": "#E64A19",
        "stops": [22, 65, 206, 62, 580, 61, 21, 48, 253, 264, 249, 12, 9, 161, 45, 140, 23],
        "time": "05:10-21:10", "freq": "20 min", "length": 26, "buses": 8
    },
]

output = []
for r in routes_raw:
    stop_details = []
    for sid in r["stops"]:
        if sid in by_id:
            s = by_id[sid]
            stop_details.append({
                "stationid": s["stationid"],
                "name": s["stationname"],
                "lat": s["latitude"],
                "lng": s["longitude"]
            })
    output.append({
        "route_id": r["id"],
        "name": r["name"],
        "description": r["desc"],
        "color": r["color"],
        "stops": stop_details,
        "schedule": {
            "time_range": r["time"],
            "frequency": r["freq"],
            "length_km": r["length"],
            "num_buses": r["buses"]
        }
    })

with open("routes.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Generated {len(output)} routes with stop details")
