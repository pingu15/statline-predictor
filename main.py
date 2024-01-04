import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import requests
import json
import csv
from collections import defaultdict

BASE_URL = 'https://api-web.nhle.com/v1'
QOT_URL = 'QOT.csv'
DATA_FILE = 'data.json'
SUPERSTAR_THRESHOLD = 0.5

QOT = defaultdict(list)
forwards = []
fwdStats = []
data = {}

def parse(player):
    print(player['playerId'])
    for season in player['seasonTotals']:
        if season['leagueAbbrev'] == 'NHL' and season['gamesPlayed'] >= 50 and season['season'] >= 20072008:
            gp = season['gamesPlayed']
            qot = 0
            if str(player['playerId']) not in QOT:
                continue
            for year in QOT[str(player['playerId'])]:
                if year[0] == season['season']:
                    qot = year[1]
                    break
            if qot == 0:
                continue
            year = {
                'id': player['playerId'],
                'season': season['season'],
                'age':  int(str(season['season'])[:4]) - int(player['birthDate'][:4]),
                'G': season['goals'],
                'A': season['assists'],
                'P': season['points'],
                'G/GP': season['goals']/gp,
                'A/GP': season['assists']/gp,
                'P/GP': season['points']/gp,
                'QoT': qot
            }
            fwdStats.append(year)

with open(f'{QOT_URL}', 'r') as f:
    fwd_set = set()
    reader = csv.reader(f)
    heading = True
    for row in reader:
        if heading:
            heading = False
            continue
        QOT[row[2]].append([int("20"+row[3].replace("-","20")), float(row[16])])
        if int(row[2]) not in fwd_set:
            forwards.append(int(row[2]))
            fwd_set.add(int(row[2]))

with open(f'{DATA_FILE}', 'r') as f:
    data = json.load(f)

if 'fwdStats' not in data:
    for forward in forwards:
        parse(requests.get(f'{BASE_URL}/player/{forward}/landing/').json())
    data = {
        'forwards': forwards,
        'fwdStats': fwdStats
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
else:
    forwards = data['forwards']
    fwdStats = data['fwdStats']

PREV_SZN_PTS = []
CUR_SZN_PTS = []
CUR_SZN_QOT = []
CUR_SZN_AGE = []

seasons = defaultdict(list)

for season in fwdStats:
    if str(season['id']) not in seasons:
        seasons[str(season['id'])] = []
    seasons[str(season['id'])].append(season)

for season in fwdStats:
    prev_szn = (int(str(season['season'])[:4])-1) * 10000 + int(str(season['season'])[:4])
    cnt_superstar_szns = 0
    for szn in seasons[str(season['id'])]:
        cnt_superstar_szns += 1 if szn['P/GP'] > SUPERSTAR_THRESHOLD else 0
    for szn in seasons[str(season['id'])]:
        if szn['season'] == prev_szn and cnt_superstar_szns > 2:
            PREV_SZN_PTS.append(szn['P/GP'])
            CUR_SZN_PTS.append(season['P/GP'])
            CUR_SZN_QOT.append(season['QoT'])
            CUR_SZN_AGE.append(season['age'])
            break

quadratic = PolynomialFeatures(degree=2, include_bias=False)
CUR_SZN_AGE = np.array(CUR_SZN_AGE).reshape(-1,1)
CUR_SZN_AGE_SQUARED = [[arr[1]] for arr in quadratic.fit_transform(CUR_SZN_AGE)]
PREV_SZN_PTS = np.array(PREV_SZN_PTS).reshape(-1,1)
CUR_SZN_PTS = np.array(CUR_SZN_PTS).reshape(-1,1)
CUR_SZN_QOT = np.array(CUR_SZN_QOT).reshape(-1,1)

TEST_PARAMS = []
PARAMS = []
for i in range(len(CUR_SZN_AGE)):
    PARAMS.append([PREV_SZN_PTS[i][0], CUR_SZN_AGE_SQUARED[i][0], CUR_SZN_QOT[i][0]])
    TEST_PARAMS.append([CUR_SZN_QOT[i][0], CUR_SZN_AGE_SQUARED[i][0]])
PARAMS = np.array(PARAMS).reshape(-1, 3)
TEST_PARAMS = np.array(TEST_PARAMS).reshape(-1, 2)


reg = LinearRegression().fit(PARAMS, CUR_SZN_PTS)
test_reg = LinearRegression().fit(TEST_PARAMS, CUR_SZN_PTS)
age_reg = LinearRegression().fit(CUR_SZN_AGE_SQUARED, CUR_SZN_PTS)

# plt.scatter(CUR_SZN_AGE, CUR_SZN_PTS)
# vals = np.linspace(19, 45, 100).reshape(-1,1)
# plt.plot(vals, age_reg.predict(quadratic.fit_transform(vals)), color='red')
# plt.show()

# print(CUR_SZN_AGE_SQUARED)

# X, Y = np.meshgrid(np.linspace(26, 34, 100).reshape(-1, 1), np.linspace(19, 45, 100).reshape(-1, 1))
# transY = []
# for i in range(len(Y)):
#     transY.append([arr[1] for arr in quadratic.fit_transform(np.array(Y[i]).reshape(-1,1))])
# transY = np.array(transY)
# TEST = []
# for i in range(len(X)):
#     for j in range(len(X[i])):
#         TEST.append([X[i][j], transY[i][j]])
# RES = test_reg.predict(TEST).reshape(X.shape)
# print(test_reg.coef_)
# ax = plt.subplot(projection='3d')
# ax.plot_surface(X, Y, RES, cmap='viridis')
# plt.show()

print('Enter current season age: ')
CUR_SZN_AGE_TEST = int(input())
print('Enter previous season games played: ')
PREV_SZN_GP_TEST = int(input())
print(f'Enter previous season points: (model trained with players averaging at least {SUPERSTAR_THRESHOLD} P/GP)')
PREV_SZN_PTS_TEST = int(input())
print('Enter QoT value: (between 25 and 34, the higher the better linemates)')
QOT_TEST = float(input())

SZN_TEST = [PREV_SZN_PTS_TEST/PREV_SZN_GP_TEST, quadratic.fit_transform([[CUR_SZN_AGE_TEST]])[0][0], QOT_TEST]
CUR_SZN_PTS_TEST = reg.predict([SZN_TEST])

print(f'Predicted 82 game pace: {round(CUR_SZN_PTS_TEST[0][0]*82, 1)} points')