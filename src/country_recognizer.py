import re
import unicodedata
from pathlib import Path

import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_FOLDER / "data" / "processed" / "news_cleaned.csv"
OUTPUT_FILE = PROJECT_FOLDER / "data" / "processed" / "news_with_countries.csv"


# ============================================================
# 2. COUNTRY / GEOPOLITICAL ENTITY ALIASES
# ============================================================
# This dictionary preserves the broad A-Z list from the previous
# version. Accented names are normalized during matching.
#
# Note: the list includes some entities beyond universally
# recognized sovereign states (for example, Palestine and Taiwan),
# plus historical/alternative names. Treat the output as detected
# geographic entities, not a definitive sovereignty classification.

COUNTRY_ALIASES = {'Afghanistan': ['Afghanistan',
                 'Afghan',
                 'Afghans',
                 'Afghani',
                 'Islamic Emirate of Afghanistan',
                 'Islamic Republic of Afghanistan'],
 'Albania': ['Albania', 'Albanian', 'Albanians', 'Republic of Albania', 'Shqiperia'],
 'Algeria': ['Algeria', 'Algerian', 'Algerians', "People's Democratic Republic of Algeria", 'Al-Jazair'],
 'Andorra': ['Andorra', 'Andorran', 'Andorrans', 'Principality of Andorra', "Principat d'Andorra"],
 'Angola': ['Angola', 'Angolan', 'Angolans', 'Republic of Angola'],
 'Antigua and Barbuda': ['Antigua and Barbuda',
                         'Antiguan',
                         'Barbudan',
                         'Antiguans',
                         'Barbudans',
                         'Antigua',
                         'Barbuda'],
 'Argentina': ['Argentina', 'Argentine', 'Argentinian', 'Argentines', 'Argentinians', 'Argentine Republic'],
 'Armenia': ['Armenia', 'Armenian', 'Armenians', 'Republic of Armenia', 'Hayastan'],
 'Australia': ['Australia',
               'Australian',
               'Australians',
               'Aussie',
               'Aussies',
               'Commonwealth of Australia',
               'Down Under'],
 'Austria': ['Austria', 'Austrian', 'Austrians', 'Republic of Austria', 'Osterreich'],
 'Azerbaijan': ['Azerbaijan',
                'Azerbaijani',
                'Azerbaijanis',
                'Azeri',
                'Azeris',
                'Republic of Azerbaijan',
                'AzÉ™rbaycan'],
 'Bahamas': ['Bahamas', 'The Bahamas', 'Bahamian', 'Bahamians', 'Commonwealth of The Bahamas'],
 'Bahrain': ['Bahrain', 'Bahraini', 'Bahrainis', 'Kingdom of Bahrain', 'Al-Bahrayn'],
 'Bangladesh': ['Bangladesh',
                'Bangladeshi',
                'Bangladeshis',
                "People's Republic of Bangladesh",
                'East Pakistan'],
 'Barbados': ['Barbados', 'Barbadian', 'Barbadians', 'Bajan', 'Bajans'],
 'Belarus': ['Belarus', 'Belarusian', 'Belarusians', 'Byelorussia', 'White Russia', 'Republic of Belarus'],
 'Belgium': ['Belgium', 'Belgian', 'Belgians', 'Kingdom of Belgium', 'Belgique', 'Belgien'],
 'Belize': ['Belize', 'Belizean', 'Belizeans', 'British Honduras'],
 'Benin': ['Benin', 'Beninese', 'Beninois', 'Republic of Benin', 'Dahomey'],
 'Bhutan': ['Bhutan', 'Bhutanese', 'Kingdom of Bhutan', 'Druk Yul'],
 'Bolivia': ['Bolivia',
             'Bolivian',
             'Bolivians',
             'Plurinational State of Bolivia',
             'Estado Plurinacional de Bolivia'],
 'Bosnia and Herzegovina': ['Bosnia and Herzegovina',
                            'Bosnia',
                            'Herzegovina',
                            'Bosnian',
                            'Bosnians',
                            'Herzegovinian',
                            'BiH'],
 'Botswana': ['Botswana', 'Motswana', 'Batswana', 'Botswanan', 'Republic of Botswana', 'Bechuanaland'],
 'Brazil': ['Brazil', 'Brazilian', 'Brazilians', 'Brasil', 'Federative Republic of Brazil'],
 'Brunei': ['Brunei', 'Bruneian', 'Bruneians', 'Brunei Darussalam', 'Nation of Brunei', 'Abode of Peace'],
 'Bulgaria': ['Bulgaria', 'Bulgarian', 'Bulgarians', 'Republic of Bulgaria', 'Balgariya'],
 'Burkina Faso': ['Burkina Faso', 'Burkinabe', 'Upper Volta'],
 'Burundi': ['Burundi', 'Burundian', 'Burundians', 'Republic of Burundi', 'Urundi'],
 'Cabo Verde': ['Cabo Verde',
                'Cape Verde',
                'Cape Verdean',
                'Cape Verdeans',
                'Cabo Verdean',
                'Republic of Cabo Verde'],
 'Cambodia': ['Cambodia', 'Cambodian', 'Cambodians', 'Khmer', 'Kingdom of Cambodia', 'Kampuchea'],
 'Cameroon': ['Cameroon', 'Cameroonian', 'Cameroonians', 'Republic of Cameroon', 'Cameroun'],
 'Canada': ['Canada', 'Canadian', 'Canadians', 'Canuck', 'Canucks', 'Dominion of Canada'],
 'Central African Republic': ['Central African Republic',
                              'Central African',
                              'Central Africans',
                              'Ubangi-Shari'],
 'Chad': ['Chad', 'Chadian', 'Chadians', 'Republic of Chad', 'Tchad'],
 'Chile': ['Chile', 'Chilean', 'Chileans', 'Republic of Chile'],
 'China': ['China', 'Chinese', "People's Republic of China", 'Mainland China', 'Zhongguo', 'Sino'],
 'Colombia': ['Colombia', 'Colombian', 'Colombians', 'Republic of Colombia'],
 'Comoros': ['Comoros', 'Comorian', 'Comorians', 'Union of the Comoros', 'Comoro Islands'],
 'Congo (Congo-Brazzaville)': ['Congo', 'Republic of the Congo', 'Congo-Brazzaville', 'Congolese'],
 'Costa Rica': ['Costa Rica', 'Costa Rican', 'Costa Ricans', 'Tico', 'Ticos', 'Republic of Costa Rica'],
 'Croatia': ['Croatia', 'Croatian', 'Croatians', 'Croat', 'Croats', 'Republic of Croatia', 'Hrvatska'],
 'Cuba': ['Cuba', 'Cuban', 'Cubans', 'Republic of Cuba'],
 'Cyprus': ['Cyprus', 'Cypriot', 'Cypriots', 'Republic of Cyprus', 'Kypros', 'KÄ±brÄ±s'],
 'Czechia': ['Czechia', 'Czech Republic', 'Czech', 'Czechs', 'Bohemia', 'ÄŒesko'],
 'Democratic Republic of the Congo': ['Democratic Republic of the Congo',
                                      'DR Congo',
                                      'Congo-Kinshasa',
                                      'Zaire',
                                      'Congolese'],
 'Denmark': ['Denmark', 'Danish', 'Dane', 'Danes', 'Kingdom of Denmark', 'Danmark'],
 'Djibouti': ['Djibouti',
              'Djiboutian',
              'Djiboutians',
              'Republic of Djibouti',
              'French Somaliland',
              'Jabuuti'],
 'Dominica': ['Dominica', 'Dominican', 'Dominicans', 'Commonwealth of Dominica', "Wai'tu kubuli"],
 'Dominican Republic': ['Dominican Republic', 'Dominican', 'Dominicans', 'Quisqueya'],
 'Ecuador': ['Ecuador', 'Ecuadorian', 'Ecuadorians', 'Republic of Ecuador'],
 'Egypt': ['Egypt', 'Egyptian', 'Egyptians', 'Arab Republic of Egypt', 'Misr', 'Masr'],
 'El Salvador': ['El Salvador', 'Salvadoran', 'Salvadorans', 'Salvadorian', 'Republic of El Salvador'],
 'Equatorial Guinea': ['Equatorial Guinea',
                       'Equatoguinean',
                       'Equatorial Guinean',
                       'Republic of Equatorial Guinea',
                       'Guinea Ecuatorial'],
 'Eritrea': ['Eritrea', 'Eritrean', 'Eritreans', 'State of Eritrea', 'Ertra'],
 'Estonia': ['Estonia', 'Estonian', 'Estonians', 'Republic of Estonia', 'Eesti'],
 'Eswatini': ['Eswatini', 'Swaziland', 'Swazi', 'Swazis', 'Liswati', 'Emaswati', 'Kingdom of Eswatini'],
 'Ethiopia': ['Ethiopia',
              'Ethiopian',
              'Ethiopians',
              'Federal Democratic Republic of Ethiopia',
              'Abyssinia',
              "Ityop'iya"],
 'Fiji': ['Fiji', 'Fijian', 'Fijians', 'Republic of Fiji', 'Viti'],
 'Finland': ['Finland', 'Finnish', 'Finn', 'Finns', 'Republic of Finland', 'Suomi'],
 'France': ['France', 'French', 'Frenchman', 'Frenchwoman', 'Frenchmen', 'French Republic'],
 'Gabon': ['Gabon', 'Gabonese', 'Gabonaise', 'Gabonese Republic'],
 'Gambia': ['Gambia', 'The Gambia', 'Gambian', 'Gambians', 'Republic of The Gambia'],
 'Georgia': ['Georgia', 'Georgian', 'Georgians', 'Sakartvelo', 'Republic of Georgia'],
 'Germany': ['Germany', 'German', 'Germans', 'Deutschland', 'Federal Republic of Germany'],
 'Ghana': ['Ghana', 'Ghanaian', 'Ghanaians', 'Republic of Ghana', 'Gold Coast'],
 'Greece': ['Greece', 'Greek', 'Greeks', 'Hellenic Republic', 'Hellas', 'Ellada'],
 'Grenada': ['Grenada', 'Grenadian', 'Grenadians', 'Spice Isle'],
 'Guatemala': ['Guatemala', 'Guatemalan', 'Guatemalans', 'Republic of Guatemala'],
 'Guinea': ['Guinea', 'Guinean', 'Guineans', 'Republic of Guinea', 'Guinea-Conakry'],
 'Guinea-Bissau': ['Guinea-Bissau',
                   'Bissau-Guinean',
                   'Bissau-Guineans',
                   'Republic of Guinea-Bissau',
                   'Portuguese Guinea'],
 'Guyana': ['Guyana', 'Guyanese', 'Co-operative Republic of Guyana', 'British Guiana'],
 'Haiti': ['Haiti', 'Haitian', 'Haitians', 'Republic of Haiti', 'Ayiti'],
 'Holy See': ['Holy See',
              'Vatican City',
              'Vatican',
              'Vatican City State',
              'State of the Vatican City',
              'Papal State'],
 'Honduras': ['Honduras', 'Honduran', 'Hondurans', 'Republic of Honduras'],
 'Hungary': ['Hungary', 'Hungarian', 'Hungarians', 'Magyar', 'Magyars'],
 'Iceland': ['Iceland', 'Icelandic', 'Icelander', 'Icelanders', 'Republic of Iceland'],
 'India': ['India', 'Indian', 'Indians', 'Republic of India', 'Bharat', 'Hindustan'],
 'Indonesia': ['Indonesia', 'Indonesian', 'Indonesians', 'Republic of Indonesia', 'Republik Indonesia'],
 'Iran': ['Iran', 'Iranian', 'Iranians', 'Islamic Republic of Iran', 'Persia', 'Persian', 'Persians'],
 'Iraq': ['Iraq', 'Iraqi', 'Iraqis', 'Republic of Iraq', 'Al-Iraq', 'Mesopotamia'],
 'Ireland': ['Ireland', 'Irish', 'Irishman', 'Irishwoman', 'Republic of Ireland', 'Eire'],
 'Israel': ['Israel', 'Israeli', 'Israelis', 'State of Israel', 'Yisrael'],
 'Italy': ['Italy', 'Italian', 'Italians', 'Italian Republic', 'Italia', 'Repubblica Italiana'],
 'Ivory Coast': ['Ivory Coast', "Cote d'Ivoire", 'Ivorian', 'Ivorians'],
 'Jamaica': ['Jamaica', 'Jamaican', 'Jamaicans', 'Commonwealth of Jamaica', 'Xaymaca'],
 'Japan': ['Japan', 'Japanese', 'Nippon', 'Nihon', 'State of Japan', 'Nippon-koku'],
 'Jordan': ['Jordan', 'Jordanian', 'Jordanians', 'Hashemite Kingdom of Jordan', 'Al-Urdunn', 'Transjordan'],
 'Kazakhstan': ['Kazakhstan', 'Kazakh', 'Kazakhs', 'Kazakhstani', 'Republic of Kazakhstan', 'Qazaqstan'],
 'Kenya': ['Kenya', 'Kenyan', 'Kenyans', 'Republic of Kenya', 'Jamhuri ya Kenya'],
 'Kiribati': ['Kiribati', 'I-Kiribati', 'Kiribatian', 'Republic of Kiribati', 'Gilbert Islands'],
 'Kuwait': ['Kuwait', 'Kuwaiti', 'Kuwaitis', 'State of Kuwait', 'Al-Kuwayt'],
 'Kyrgyzstan': ['Kyrgyzstan', 'Kyrgyz', 'Kirghiz', 'Kyrgyzstani', 'Kyrgyz Republic', 'Kirghizia'],
 'Laos': ['Laos', 'Lao', 'Laotian', 'Laotians', "Lao People's Democratic Republic", 'Lao PDR'],
 'Latvia': ['Latvia', 'Latvian', 'Latvians', 'Lett', 'Letts', 'Republic of Latvia', 'Latvija'],
 'Lebanon': ['Lebanon', 'Lebanese', 'Lebanese Republic', 'Lubnan', 'Al-Lubnan'],
 'Lesotho': ['Lesotho', 'Mosotho', 'Basotho', 'Lesothan', 'Kingdom of Lesotho', 'Basutoland'],
 'Liberia': ['Liberia', 'Liberian', 'Liberians', 'Republic of Liberia'],
 'Libya': ['Libya', 'Libyan', 'Libyans', 'State of Libya', 'Libiyah'],
 'Liechtenstein': ['Liechtenstein', 'Liechtensteiner', 'Liechtensteiners', 'Principality of Liechtenstein'],
 'Lithuania': ['Lithuania', 'Lithuanian', 'Lithuanians', 'Republic of Lithuania', 'Lietuva'],
 'Luxembourg': ['Luxembourg', 'Luxembourger', 'Luxembourgers', 'Luxembourgish', 'Grand Duchy of Luxembourg'],
 'Madagascar': ['Madagascar', 'Malagasy', 'Madagascan', 'Republic of Madagascar', 'Madagasikara'],
 'Malawi': ['Malawi', 'Malawian', 'Malawians', 'Republic of Malawi', 'Nyasaland'],
 'Malaysia': ['Malaysia', 'Malaysian', 'Malaysians', 'Malay', 'Federation of Malaysia', 'Malaya'],
 'Maldives': ['Maldives', 'Maldivian', 'Maldivians', 'Republic of Maldives', 'Dhivehi Raajje'],
 'Mali': ['Mali', 'Malian', 'Malians', 'Republic of Mali', 'French Sudan'],
 'Malta': ['Malta', 'Maltese', 'Republic of Malta', "Repubblika ta' Malta"],
 'Marshall Islands': ['Marshall Islands', 'Marshallese', 'Republic of the Marshall Islands'],
 'Mauritania': ['Mauritania', 'Mauritanian', 'Mauritanians', 'Islamic Republic of Mauritania', 'Muritanya'],
 'Mauritius': ['Mauritius', 'Mauritian', 'Mauritians', 'Republic of Mauritius', 'Maurice'],
 'Mexico': ['Mexico', 'Mexican', 'Mexicans', 'United Mexican States', 'Estados Unidos Mexicanos'],
 'Micronesia': ['Micronesia', 'Micronesian', 'Micronesians', 'Federated States of Micronesia'],
 'Moldova': ['Moldova', 'Moldovan', 'Moldovans', 'Republic of Moldova', 'Bessarabia'],
 'Monaco': ['Monaco', 'Monegasque', 'Monacan', 'Principality of Monaco'],
 'Mongolia': ['Mongolia', 'Mongolian', 'Mongolians', 'Mongol', 'Mongols', 'Outer Mongolia'],
 'Montenegro': ['Montenegro', 'Montenegrin', 'Montenegrins', 'Crna Gora'],
 'Morocco': ['Morocco', 'Moroccan', 'Moroccans', 'Kingdom of Morocco', 'Al-Maghrib', 'Maroc'],
 'Mozambique': ['Mozambique', 'Mozambican', 'Mozambicans', 'Republic of Mozambique'],
 'Myanmar': ['Myanmar', 'Burma', 'Burmese', 'Myanma', 'Republic of the Union of Myanmar'],
 'Namibia': ['Namibia', 'Namibian', 'Namibians', 'Republic of Namibia', 'South West Africa'],
 'Nauru': ['Nauru', 'Nauruan', 'Nauruans', 'Republic of Nauru', 'Pleasant Island'],
 'Nepal': ['Nepal', 'Nepali', 'Nepalis', 'Nepalese', 'Federal Democratic Republic of Nepal'],
 'Netherlands': ['Netherlands',
                 'The Netherlands',
                 'Dutch',
                 'Dutchman',
                 'Dutchwoman',
                 'Holland',
                 'Kingdom of the Netherlands',
                 'Nederland'],
 'New Zealand': ['New Zealand', 'New Zealander', 'New Zealanders', 'Kiwi', 'Kiwis', 'Aotearoa'],
 'Nicaragua': ['Nicaragua', 'Nicaraguan', 'Nicaraguans', 'Republic of Nicaragua'],
 'Niger': ['Niger', 'Nigerien', 'Nigeriens', 'Republic of the Niger'],
 'Nigeria': ['Nigeria', 'Nigerian', 'Nigerians', 'Federal Republic of Nigeria'],
 'North Korea': ['North Korea',
                 'North Korean',
                 'North Koreans',
                 "Democratic People's Republic of Korea",
                 'Choson'],
 'North Macedonia': ['North Macedonia',
                     'Macedonia',
                     'Macedonian',
                     'Macedonians',
                     'Republic of North Macedonia',
                     'Severna Makedonija'],
 'Norway': ['Norway', 'Norwegian', 'Norwegians', 'Kingdom of Norway', 'Norge', 'Noreg'],
 'Oman': ['Oman', 'Omani', 'Omanis', 'Sultanate of Oman', 'Uman'],
 'Pakistan': ['Pakistan', 'Pakistani', 'Pakistanis', 'Islamic Republic of Pakistan', 'West Pakistan'],
 'Palau': ['Palau', 'Palauan', 'Palauans', 'Republic of Palau', 'Belau'],
 'Palestine': ['Palestine',
               'Palestinian',
               'Palestinians',
               'State of Palestine',
               'Filastin',
               'Occupied Palestinian Territory'],
 'Panama': ['Panama', 'Panamanian', 'Panamanians', 'Republic of Panama'],
 'Papua New Guinea': ['Papua New Guinea',
                      'Papua New Guinean',
                      'Papuan',
                      'Independent State of Papua New Guinea'],
 'Paraguay': ['Paraguay', 'Paraguayan', 'Paraguayans', 'Republic of Paraguay'],
 'Peru': ['Peru', 'Peruvian', 'Peruvians', 'Republic of Peru'],
 'Philippines': ['Philippines',
                 'The Philippines',
                 'Filipino',
                 'Filipinos',
                 'Filipina',
                 'Philippine',
                 'Republic of the Philippines',
                 'Pilipinas'],
 'Poland': ['Poland', 'Polish', 'Pole', 'Poles', 'Republic of Poland', 'Polska'],
 'Portugal': ['Portugal', 'Portuguese', 'Portuguese Republic', 'Lusitania'],
 'Qatar': ['Qatar', 'Qatari', 'Qataris', 'State of Qatar', 'Dawlat Qatar'],
 'Romania': ['Romania', 'Romanian', 'Romanians', 'Rumania'],
 'Russia': ['Russia', 'Russian', 'Russians', 'Russian Federation', 'Rossiya', 'Soviet Union'],
 'Rwanda': ['Rwanda', 'Rwandan', 'Rwandans', 'Rwandese', 'Republic of Rwanda', 'Ruanda'],
 'Saint Kitts and Nevis': ['Saint Kitts and Nevis',
                           'St. Kitts and Nevis',
                           'Kittitian',
                           'Nevisian',
                           'Federation of Saint Christopher and Nevis'],
 'Saint Lucia': ['Saint Lucia', 'St. Lucia', 'Saint Lucian', 'Saint Lucians', 'Lucian'],
 'Saint Vincent and the Grenadines': ['Saint Vincent and the Grenadines',
                                      'St. Vincent and the Grenadines',
                                      'Vincentian',
                                      'Vincentians',
                                      'Vincy'],
 'Samoa': ['Samoa', 'Samoan', 'Samoans', 'Independent State of Samoa', 'Western Samoa'],
 'San Marino': ['San Marino', 'Sammarinese', 'Republic of San Marino', 'Most Serene Republic of San Marino'],
 'Sao Tome and Principe': ['Sao Tome and Principe', 'Sao Tomean', 'Santomean'],
 'Saudi Arabia': ['Saudi Arabia',
                  'Saudi',
                  'Saudis',
                  'Saudi Arabian',
                  'Kingdom of Saudi Arabia',
                  "As-Su'udiyyah"],
 'Senegal': ['Senegal', 'Senegalese', 'Republic of Senegal'],
 'Serbia': ['Serbia', 'Serbian', 'Serbians', 'Serb', 'Serbs', 'Republic of Serbia', 'Srbija'],
 'Seychelles': ['Seychelles', 'Seychellois', 'Seychelloise', 'Republic of Seychelles', 'Sesel'],
 'Sierra Leone': ['Sierra Leone', 'Sierra Leonean', 'Sierra Leoneans', 'Republic of Sierra Leone', 'Salone'],
 'Singapore': ['Singapore', 'Singaporean', 'Singaporeans', 'Republic of Singapore', 'Singapura', 'Lion City'],
 'Slovakia': ['Slovakia', 'Slovak', 'Slovaks', 'Slovakian', 'Slovak Republic', 'Slovensko'],
 'Slovenia': ['Slovenia',
              'Slovenian',
              'Slovenians',
              'Slovene',
              'Slovenes',
              'Republic of Slovenia',
              'Slovenija'],
 'Solomon Islands': ['Solomon Islands', 'Solomon Islander', 'Solomon Islanders', 'Solomons'],
 'Somalia': ['Somalia', 'Somali', 'Somalis', 'Somalian', 'Federal Republic of Somalia', 'Soomaaliya'],
 'South Africa': ['South Africa', 'South African', 'South Africans', 'Republic of South Africa', 'Mzansi'],
 'South Korea': ['South Korea',
                 'South Korean',
                 'South Koreans',
                 'Korea',
                 'Korean',
                 'Republic of Korea',
                 'Hanguk'],
 'South Sudan': ['South Sudan', 'South Sudanese', 'Republic of South Sudan', 'Southern Sudan'],
 'Spain': ['Spain', 'Spanish', 'Spaniard', 'Spaniards', 'Kingdom of Spain', 'Espana'],
 'Sri Lanka': ['Sri Lanka',
               'Sri Lankan',
               'Sri Lankans',
               'Ceylon',
               'Ceylonese',
               'Democratic Socialist Republic of Sri Lanka'],
 'Sudan': ['Sudan', 'Sudanese', 'Republic of the Sudan', 'North Sudan', 'As-Sudan'],
 'Suriname': ['Suriname', 'Surinamese', 'Republic of Suriname', 'Dutch Guiana'],
 'Sweden': ['Sweden', 'Swedish', 'Swede', 'Swedes', 'Kingdom of Sweden', 'Sverige'],
 'Switzerland': ['Switzerland', 'Swiss', 'Swiss Confederation', 'Schweiz', 'Suisse', 'Svizzera', 'Helvetia'],
 'Syria': ['Syria', 'Syrian', 'Syrians', 'Syrian Arab Republic', 'Suriyah'],
 'Taiwan': ['Taiwan', 'Taiwanese', 'Republic of China', 'Chinese Taipei', 'Formosa'],
 'Tajikistan': ['Tajikistan', 'Tajik', 'Tajiks', 'Tajikistani', 'Republic of Tajikistan', 'Tojikiston'],
 'Tanzania': ['Tanzania', 'Tanzanian', 'Tanzanians', 'United Republic of Tanzania', 'Tanganyika', 'Zanzibar'],
 'Thailand': ['Thailand', 'Thai', 'Thais', 'Kingdom of Thailand', 'Siam', 'Siamese', 'Prathet Thai'],
 'Timor-Leste': ['Timor-Leste',
                 'East Timor',
                 'Timorese',
                 'East Timorese',
                 'Democratic Republic of Timor-Leste'],
 'Togo': ['Togo', 'Togolese', 'Togolese Republic', 'Togoland'],
 'Tonga': ['Tonga', 'Tongan', 'Tongans', 'Kingdom of Tonga', 'Friendly Islands'],
 'Trinidad and Tobago': ['Trinidad and Tobago',
                         'Trinidadian',
                         'Tobagonian',
                         'Trinbagonian',
                         'Trini',
                         'Republic of Trinidad and Tobago'],
 'Tunisia': ['Tunisia', 'Tunisian', 'Tunisians', 'Republic of Tunisia', 'Tunis', 'Tunisiyah'],
 'Turkey': ['Turkey', 'Turkiye', 'Turkish', 'Turk', 'Turks', 'Republic of Turkey'],
 'Turkmenistan': ['Turkmenistan', 'Turkmen', 'Turkmens', 'Turkmenistani'],
 'Tuvalu': ['Tuvalu', 'Tuvaluan', 'Tuvaluans', 'Ellice Islands'],
 'Uganda': ['Uganda', 'Ugandan', 'Ugandans', 'Republic of Uganda'],
 'Ukraine': ['Ukraine', 'Ukrainian', 'Ukrainians', 'Ukraina'],
 'United Arab Emirates': ['United Arab Emirates', 'U.A.E.', 'Emirati', 'Emiratis', 'Emirates', 'Al-Imarat'],
 'United Kingdom': ['United Kingdom',
                    'U.K.',
                    'Britain',
                    'Great Britain',
                    'British',
                    'Briton',
                    'Britons',
                    'England'],
 'United States': ['United States',
                   'U.S.A.',
                   'U.S.',
                   'America',
                   'American',
                   'Americans',
                   'United States of America'],
 'Uruguay': ['Uruguay', 'Uruguayan', 'Uruguayans', 'Oriental Republic of Uruguay'],
 'Uzbekistan': ['Uzbekistan', 'Uzbek', 'Uzbeks', 'Uzbekistani', 'Republic of Uzbekistan', "O'zbekiston"],
 'Vanuatu': ['Vanuatu', 'Ni-Vanuatu', 'Vanuatuan', 'Republic of Vanuatu', 'New Hebrides'],
 'Venezuela': ['Venezuela', 'Venezuelan', 'Venezuelans', 'Bolivarian Republic of Venezuela'],
 'Vietnam': ['Vietnam', 'Viet Nam', 'Vietnamese', 'Socialist Republic of Vietnam', 'Viá»‡t Nam'],
 'Yemen': ['Yemen', 'Yemeni', 'Yemenis', 'Yemenite', 'Republic of Yemen', 'Al-Yaman'],
 'Zambia': ['Zambia', 'Zambian', 'Zambians', 'Republic of Zambia', 'Northern Rhodesia'],
 'Zimbabwe': ['Zimbabwe', 'Zimbabwean', 'Zimbabweans', 'Zimbo', 'Republic of Zimbabwe', 'Rhodesia']}


# Short uppercase codes and abbreviations are matched separately.
# Matching is case-sensitive, so "IN" can match as a code but the
# ordinary word "in" will not.
CODE_ALIASES = {'Afghanistan': ['AFG', 'AF'],
 'Albania': ['ALB', 'AL'],
 'Algeria': ['DZA', 'DZ'],
 'Andorra': ['AND', 'AD'],
 'Angola': ['AGO', 'AO'],
 'Antigua and Barbuda': ['ATG', 'AG'],
 'Argentina': ['ARG', 'AR'],
 'Armenia': ['ARM', 'AM'],
 'Australia': ['AUS', 'AU'],
 'Austria': ['AUT', 'AT'],
 'Azerbaijan': ['AZE', 'AZ'],
 'Bahamas': ['BHS', 'BS'],
 'Bahrain': ['BHR', 'BH'],
 'Bangladesh': ['BGD', 'BD'],
 'Barbados': ['BRB', 'BB'],
 'Belarus': ['BLR', 'BY'],
 'Belgium': ['BEL', 'BE'],
 'Belize': ['BLZ', 'BZ'],
 'Benin': ['BEN', 'BJ'],
 'Bhutan': ['BTN', 'BT'],
 'Bolivia': ['BOL', 'BO'],
 'Bosnia and Herzegovina': ['BIH', 'BA'],
 'Botswana': ['BWA', 'BW'],
 'Brazil': ['BRA', 'BR'],
 'Brunei': ['BRN', 'BN'],
 'Bulgaria': ['BGR', 'BG'],
 'Burkina Faso': ['BFA', 'BF'],
 'Burundi': ['BDI', 'BI'],
 'Cabo Verde': ['CPV', 'CV'],
 'Cambodia': ['KHM', 'KH'],
 'Cameroon': ['CMR', 'CM'],
 'Canada': ['CAN', 'CA'],
 'Central African Republic': ['CAR', 'CAF', 'CF'],
 'Chad': ['TCD', 'TD'],
 'Chile': ['CHL', 'CL'],
 'China': ['PRC', 'CHN', 'CN'],
 'Colombia': ['COL', 'CO'],
 'Comoros': ['COM', 'KM'],
 'Congo (Congo-Brazzaville)': ['RC', 'COG', 'CG'],
 'Costa Rica': ['CRI', 'CR'],
 'Croatia': ['HRV', 'HR'],
 'Cuba': ['CUB', 'CU'],
 'Cyprus': ['CYP', 'CY'],
 'Czechia': ['CZE', 'CZ'],
 'Democratic Republic of the Congo': ['DRC', 'DROC', 'COD', 'CD'],
 'Denmark': ['DNK', 'DK'],
 'Djibouti': ['DJI', 'DJ'],
 'Dominica': ['DMA', 'DM'],
 'Dominican Republic': ['DR', 'DOM', 'DO'],
 'Ecuador': ['ECU', 'EC'],
 'Egypt': ['EGY', 'EG'],
 'El Salvador': ['SLV', 'SV'],
 'Equatorial Guinea': ['GNQ', 'GQ'],
 'Eritrea': ['ERI', 'ER'],
 'Estonia': ['EST', 'EE'],
 'Eswatini': ['SWZ', 'SZ'],
 'Ethiopia': ['ETH', 'ET'],
 'Fiji': ['FJI', 'FJ'],
 'Finland': ['FIN', 'FI'],
 'France': ['FRA', 'FR'],
 'Gabon': ['GAB', 'GA'],
 'Gambia': ['GMB', 'GM'],
 'Georgia': ['GEO', 'GE'],
 'Germany': ['FRG', 'BRD', 'DEU', 'DE'],
 'Ghana': ['GHA', 'GH'],
 'Greece': ['GRC', 'GR'],
 'Grenada': ['GRD', 'GD'],
 'Guatemala': ['GTM', 'GT'],
 'Guinea': ['GIN', 'GN'],
 'Guinea-Bissau': ['GNB', 'GW'],
 'Guyana': ['GUY', 'GY'],
 'Haiti': ['HTI', 'HT'],
 'Holy See': ['VAT', 'VA'],
 'Honduras': ['HND', 'HN'],
 'Hungary': ['HUN', 'HU'],
 'Iceland': ['ISL', 'IS'],
 'India': ['IND', 'IN'],
 'Indonesia': ['IDN', 'ID'],
 'Iran': ['IRN', 'IR'],
 'Iraq': ['IRQ', 'IQ'],
 'Ireland': ['IRL', 'IE'],
 'Israel': ['ISR', 'IL'],
 'Italy': ['ITA', 'IT'],
 'Ivory Coast': ['CIV', 'CI'],
 'Jamaica': ['JAM', 'JM'],
 'Japan': ['JPN', 'JP'],
 'Jordan': ['JOR', 'JO'],
 'Kazakhstan': ['KAZ', 'KZ'],
 'Kenya': ['KEN', 'KE'],
 'Kiribati': ['KIR', 'KI'],
 'Kuwait': ['KWT', 'KW'],
 'Kyrgyzstan': ['KGZ', 'KG'],
 'Laos': ['LAO', 'LA'],
 'Latvia': ['LVA', 'LV'],
 'Lebanon': ['LBN', 'LB'],
 'Lesotho': ['LSO', 'LS'],
 'Liberia': ['LBR', 'LR'],
 'Libya': ['LBY', 'LY'],
 'Liechtenstein': ['LIE', 'LI'],
 'Lithuania': ['LTU', 'LT'],
 'Luxembourg': ['LUX', 'LU'],
 'Madagascar': ['MDG', 'MG'],
 'Malawi': ['MWI', 'MW'],
 'Malaysia': ['MYS', 'MY'],
 'Maldives': ['MDV', 'MV'],
 'Mali': ['MLI', 'ML'],
 'Malta': ['MLT', 'MT'],
 'Marshall Islands': ['RMI', 'MHL', 'MH'],
 'Mauritania': ['MRT', 'MR'],
 'Mauritius': ['MUS', 'MU'],
 'Mexico': ['MEX', 'MX'],
 'Micronesia': ['FSM', 'FM'],
 'Moldova': ['MDA', 'MD'],
 'Monaco': ['MCO', 'MC'],
 'Mongolia': ['MNG', 'MN'],
 'Montenegro': ['MNE', 'ME'],
 'Morocco': ['MAR', 'MA'],
 'Mozambique': ['MOZ', 'MZ'],
 'Myanmar': ['MMR', 'MM'],
 'Namibia': ['NAM', 'NA'],
 'Nauru': ['NRU', 'NR'],
 'Nepal': ['NPL', 'NP'],
 'Netherlands': ['NLD', 'NL'],
 'New Zealand': ['NZL', 'NZ'],
 'Nicaragua': ['NIC', 'NI'],
 'Niger': ['NER', 'NE'],
 'Nigeria': ['NGA', 'NG'],
 'North Korea': ['DPRK', 'PRK', 'KP'],
 'North Macedonia': ['FYROM', 'MKD', 'MK'],
 'Norway': ['NOR', 'NO'],
 'Oman': ['OMN', 'OM'],
 'Pakistan': ['PAK', 'PK'],
 'Palau': ['PLW', 'PW'],
 'Palestine': ['PSE', 'PS'],
 'Panama': ['PAN', 'PA'],
 'Papua New Guinea': ['PNG', 'PG'],
 'Paraguay': ['PRY', 'PY'],
 'Peru': ['PER', 'PE'],
 'Philippines': ['PHL', 'PH'],
 'Poland': ['POL', 'PL'],
 'Portugal': ['PRT', 'PT'],
 'Qatar': ['QAT', 'QA'],
 'Romania': ['ROU', 'RO'],
 'Russia': ['USSR', 'RUS', 'RU'],
 'Rwanda': ['RWA', 'RW'],
 'Saint Kitts and Nevis': ['KNA', 'KN'],
 'Saint Lucia': ['LCA', 'LC'],
 'Saint Vincent and the Grenadines': ['VCT', 'VC'],
 'Samoa': ['WSM', 'WS'],
 'San Marino': ['SMR', 'SM'],
 'Sao Tome and Principe': ['STP', 'ST'],
 'Saudi Arabia': ['KSA', 'SAU', 'SA'],
 'Senegal': ['SEN', 'SN'],
 'Serbia': ['SRB', 'RS'],
 'Seychelles': ['SYC', 'SC'],
 'Sierra Leone': ['SLE', 'SL'],
 'Singapore': ['SGP', 'SG'],
 'Slovakia': ['SVK', 'SK'],
 'Slovenia': ['SVN', 'SI'],
 'Solomon Islands': ['SLB', 'SB'],
 'Somalia': ['SOM', 'SO'],
 'South Africa': ['RSA', 'ZAF', 'ZA'],
 'South Korea': ['ROK', 'KOR', 'KR'],
 'South Sudan': ['SSD', 'SS'],
 'Spain': ['ESP', 'ES'],
 'Sri Lanka': ['LKA', 'LK'],
 'Sudan': ['SDN', 'SD'],
 'Suriname': ['SUR', 'SR'],
 'Sweden': ['SWE', 'SE'],
 'Switzerland': ['CHE', 'CH'],
 'Syria': ['SYR', 'SY'],
 'Taiwan': ['ROC', 'TWN', 'TW'],
 'Tajikistan': ['TJK', 'TJ'],
 'Tanzania': ['TZA', 'TZ'],
 'Thailand': ['THA', 'TH'],
 'Timor-Leste': ['TLS', 'TL'],
 'Togo': ['TGO', 'TG'],
 'Tonga': ['TON', 'TO'],
 'Trinidad and Tobago': ['TTO', 'TT'],
 'Tunisia': ['TUN', 'TN'],
 'Turkey': ['TUR', 'TR'],
 'Turkmenistan': ['TKM', 'TM'],
 'Tuvalu': ['TUV', 'TV'],
 'Uganda': ['UGA', 'UG'],
 'Ukraine': ['UKR', 'UA'],
 'United Arab Emirates': ['UAE', 'ARE', 'AE'],
 'United Kingdom': ['UK', 'GBR', 'GB'],
 'United States': ['USA', 'US'],
 'Uruguay': ['URY', 'UY'],
 'Uzbekistan': ['UZB', 'UZ'],
 'Vanuatu': ['VUT', 'VU'],
 'Venezuela': ['VEN', 'VE'],
 'Vietnam': ['VNM', 'VN'],
 'Yemen': ['YEM', 'YE'],
 'Zambia': ['ZMB', 'ZM'],
 'Zimbabwe': ['ZWE', 'ZW']}


# ============================================================
# CITY AND REGIONAL ALIASES
# These locations map to their associated countries.
# ============================================================

CITY_ALIASES = {
   # --- A ---
    "Afghanistan": [
        "Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad", 
        "Kunduz", "Ghazni", "Balkh", "Baghlan", "Gardez", "Khost", "Bamyan"
    ],
    "Albania": [
        "Tirana", "Durres", "Vlore", "Elbasan", "Shkoder", 
        "Fier", "Korce", "Berat", "Lushnje", "Pogradec", "Kavaje"
    ],
    "Algeria": [
        "Algiers", "Oran", "Constantine", "Annaba", "Blida", 
        "Batna", "Djelfa", "Setif", "Sidi Bel Abbes", "Biskra", "Tebessa", "Tlemcen"
    ],
    "Andorra": [
        "Andorra la Vella", "Escaldes-Engordany", "Encamp", "Sant Julia de Loria", 
        "La Massana", "Santa Coloma", "Ordino", "Canillo", "El Pas de la Casa", "Arinsal"
    ],
    "Angola": [
        "Luanda", "Lubango", "Huambo", "Benguela", "Cabinda", 
        "Malanje", "Lobito", "Kuito", "Uige", "Saurimo", "Namibe"
    ],
    "Antigua and Barbuda": [
        "St. John's", "All Saints", "Liberta", "Potters Village", "Bolans", 
        "Swetes", "Seaview Farm", "Piggotts", "Parham", "Codrington"
    ],
    "Argentina": [
        "Buenos Aires", "Cordoba", "Rosario", "Mendoza", "San Miguel de Tucuman",
        "La Plata", "Mar del Plata", "Salta", "Santa Fe", "San Juan",
        "Resistencia", "Santiago del Estero", "Corrientes", "Posadas", "San Salvador de Jujuy",
        "Bahia Blanca", "Parana", "Neuquen", "Formosa", "San Luis",
        "La Rioja", "Catamarca", "Rio Gallegos", "Ushuaia", "Bariloche",
        "Comodoro Rivadavia", "Quilmes", "Lanus", "Merlo", "Tigre", "Patagonia"
    ],
    "Armenia": [
        "Yerevan", "Gyumri", "Vanadzor", "Vagharshapat", "Abovyan", 
        "Kapan", "Hrazdan", "Armavir", "Artashat", "Ijevan", "Goris"
    ],
    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Gold Coast", "Canberra", "Newcastle", "Wollongong", "Logan City",
        "Geelong", "Hobart", "Townsville", "Cairns", "Toowoomba",
        "Darwin", "Ballarat", "Bendigo", "Albury", "Launceston",
        "Mackay", "Rockhampton", "Bunbury", "Bundaberg", "Coffs Harbour",
        "Wagga Wagga", "Hervey Bay", "Mildura", "Shepparton", "Port Macquarie",
        "New South Wales", "Victoria", "Queensland", "Tasmania"
    ],
    "Austria": [
        "Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", 
        "Klagenfurt", "Villach", "Wels", "Sankt Polten", "Dornbirn", "Steyr", "Bregenz"
    ],
    "Azerbaijan": [
        "Baku", "Ganja", "Sumqayit", "Mingachevir", "Lankaran", 
        "Shirvan", "Nakhchivan", "Shaki", "Yevlakh", "Khankendi", "Quba"
    ],

    # --- B ---
    "Bahamas": [
        "Nassau", "Freeport", "West End", "Coopers Town", "Marsh Harbour", 
        "High Rock", "Andros Town", "Clarence Town", "Dunmore Town", "George Town"
    ],
    "Bahrain": [
        "Manama", "Riffa", "Muharraq", "Hamad Town", "Isa Town", 
        "Sitra", "Budaiya", "Jidhafs", "Al-Malikiyah", "Adliya"
    ],
    "Bangladesh": [
        "Dhaka", "Chittagong", "Chattogram", "Khulna", "Rajshahi",
        "Sylhet", "Barisal", "Rangpur", "Comilla", "Narayanganj",
        "Gazipur", "Mymensingh", "Bogra", "Cox's Bazar", "Jessore",
        "Dinajpur", "Brahmanbaria", "Tangail", "Nawabganj", "Pabna",
        "Jamalpur", "Faridpur", "Kushtia", "Noakhali", "Feni",
        "Sirajganj", "Narsingdi", "Savar", "Tongi", "Kishoreganj", "Saidpur"
    ],
    "Barbados": [
        "Bridgetown", "Speightstown", "Oistins", "Bathsheba", "Holetown", 
        "Crane", "Hastings", "Worthing", "Saint Lawrence Gap", "Six Cross Roads"
    ],
    "Belarus": [
        "Minsk", "Gomel", "Mogilev", "Vitebsk", "Grodno", 
        "Brest", "Babruysk", "Baranavichy", "Barysaw", "Pinsk", "Orsha", "Mazyr"
    ],
    "Belgium": [
        "Brussels", "Antwerp", "Ghent", "Charleroi", "Liege", 
        "Bruges", "Namur", "Leuven", "Mons", "Aalst", "Mechelen", "Ostend", "Flanders", "Wallonia"
    ],
    "Belize": [
        "Belize City", "San Ignacio", "Belmopan", "Orange Walk Town", "Corozal Town", 
        "Dangriga", "Benque Viejo del Carmen", "Punta Gorda", "San Pedro", "Ladyville"
    ],
    "Benin": [
        "Cotonou", "Porto-Novo", "Parakou", "Djougou", "Bohicon", 
        "Kandi", "Lokossa", "Ouidah", "Abomey", "Natitingou"
    ],
    "Bhutan": [
        "Thimphu", "Phuntsholing", "Paro", "Gelephu", "Samdrup Jongkhar", 
        "Wangdue Phodrang", "Punakha", "Jakar", "Trongsa", "Mongar"
    ],
    "Bolivia": [
        "Santa Cruz de la Sierra", "El Alto", "La Paz", "Cochabamba", "Oruro", 
        "Sucre", "Tarija", "Potosi", "Sacaba", "Quillacollo", "Trinidad"
    ],
    "Bosnia and Herzegovina": [
        "Sarajevo", "Banja Luka", "Tuzla", "Zenica", "Mostar", 
        "Bijeljina", "Brcko", "Prijedor", "Doboj", "Cazin", "Bihac"
    ],
    "Botswana": [
        "Gaborone", "Francistown", "Molepolole", "Maun", "Mogoditshane", 
        "Serowe", "Selibe Phikwe", "Kanye", "Mochudi", "Mahalapye"
    ],
    "Brazil": [
        "Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza",
        "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Goiania",
        "Belem", "Porto Alegre", "Guarulhos", "Campinas", "Sao Luis",
        "Sao Goncalo", "Maceio", "Duque de Caxias", "Campo Grande", "Natal",
        "Teresina", "Sao Bernardo do Campo", "Nova Iguacu", "Joao Pessoa", "Santo Andre",
        "Osasco", "Jaboatao dos Guararapes", "Ribeirao Preto", "Uberlandia", "Sorocaba",
        "Contagem", "Aracaju", "Feira de Santana", "Cuiaba", "Florianopolis"
    ],
    "Brunei": [
        "Bandar Seri Begawan", "Kuala Belait", "Seria", "Tutong", "Bangar", 
        "Muara", "Jerudong", "Lumut", "Sengkurong", "Gadong"
    ],
    "Bulgaria": [
        "Sofia", "Plovdiv", "Varna", "Burgas", "Ruse", 
        "Stara Zagora", "Pleven", "Sliven", "Dobrich", "Shumen", "Pernik"
    ],
    "Burkina Faso": [
        "Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Ouahigouya", "Banfora", 
        "Dedougou", "Kaya", "Tenkodogo", "Fada N'gourma", "Hounde"
    ],
    "Burundi": [
        "Bujumbura", "Gitega", "Muyinga", "Ngozi", "Ruyigi", 
        "Kayanza", "Bururi", "Rutana", "Muramvya", "Makamba"
    ],

    # --- C ---
    "Cabo Verde": [
        "Praia", "Mindelo", "Santa Maria", "Assomada", "Pedra Badejo", 
        "Sao Filipe", "Tarrafal", "Espargos", "Porto Novo", "Ribeira Grande"
    ],
    "Cambodia": [
        "Phnom Penh", "Siem Reap", "Battambang", "Sihanoukville", "Poipet", 
        "Ta Khmau", "Kampong Cham", "Pursat", "Kampong Speu", "Kampot"
    ],
    "Cameroon": [
        "Douala", "Yaounde", "Bamenda", "Bafoussam", "Garoua", 
        "Maroua", "Ngaoundere", "Kumba", "Nkongsamba", "Buea", "Limbe"
    ],
    "Canada": [
        "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Quebec City", "Kitchener",
        "London", "Victoria", "Halifax", "Oshawa", "Windsor",
        "Saskatoon", "St. Catharines", "Regina", "St. John's", "Kelowna",
        "Barrie", "Sherbrooke", "Guelph", "Kanata", "Abbotsford",
        "Trois-Rivieres", "Kingston", "Milton", "Moncton", "White Rock",
        "Ontario", "Quebec", "British Columbia", "Alberta"
    ],
    "Central African Republic": [
        "Bangui", "Bimbo", "Berberati", "Carnot", "Bambari", 
        "Bouar", "Bria", "Bossangoa", "Nola", "Bangassou"
    ],
    "Chad": [
        "N'Djamena", "Moundou", "Sarh", "Abeche", "Kelo", 
        "Koumra", "Pala", "Am Timan", "Bongor", "Mongo"
    ],
    "Chile": [
        "Santiago", "Valparaiso", "Concepcion", "La Serena", "Antofagasta",
        "Temuco", "Rancagua", "Talca", "Arica", "Chillan",
        "Puerto Montt", "Iquique", "Coquimbo", "Osorno", "Valdivia",
        "Quilpue", "Villa Alemana", "Los Angeles", "Calama", "Copiapo",
        "Punta Arenas", "Quillota", "Curico", "Ovalle", "Linares",
        "San Antonio", "Melipilla", "Vina del Mar", "Talcahuano", "Pudahuel"
    ],
    "China": [
        "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
        "Chongqing", "Tianjin", "Wuhan", "Dongguan", "Xi'an",
        "Hangzhou", "Foshan", "Nanjing", "Shenyang", "Harbin",
        "Qingdao", "Dalian", "Jinan", "Zhengzhou", "Changsha",
        "Kunming", "Changchun", "Urumqi", "Shantou", "Hefei",
        "Shijiazhuang", "Ningbo", "Taiyuan", "Nanning", "Xiamen",
        "Fuzhou", "Wuxi", "Suzhou", "Lhasa", "Hong Kong", "Macau"
    ],
    "Colombia": [
        "Bogota", "Medellin", "Cali", "Barranquilla", "Cartagena",
        "Cucuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibague",
        "Pasto", "Manizales", "Neiva", "Villavicencio", "Armenia",
        "Valledupar", "Monteria", "Sincelejo", "Popayan", "Floridablanca",
        "Palmira", "Buenaventura", "Barrancabermeja", "Tulua", "Envigado",
        "Dosquebradas", "Riohacha", "Tunja", "Florencia", "Soacha"
    ],
    "Comoros": [
        "Moroni", "Mutsamudu", "Fomboni", "Domoni", "Tsimbeo", 
        "Adda-Doueni", "Sima", "Ouani", "Mirontsi", "Mkazi"
    ],
    "Congo (Congo-Brazzaville)": [
        "Brazzaville", "Pointe-Noire", "Dolisie", "Nkayi", "Impfondo", 
        "Ouesso", "Madingou", "Owando", "Sibiti", "Loutete"
    ],
    "Costa Rica": [
        "San Jose", "Alajuela", "Cartago", "Heredia", "Liberia", 
        "Puntarenas", "Limon", "San Isidro", "Curridabat", "San Vicente"
    ],
    "Croatia": [
        "Zagreb", "Split", "Rijeka", "Osijek", "Zadar", 
        "Pula", "Slavonski Brod", "Karlovac", "Varazdin", "Sibenik", "Dubrovnik"
    ],
    "Cuba": [
        "Havana", "Santiago de Cuba", "Camaguey", "Holguin", "Guantanamo", 
        "Santa Clara", "Las Tunas", "Bayamo", "Cienfuegos", "Pinar del Rio", "Matanzas"
    ],
    "Cyprus": [
        "Nicosia", "Limassol", "Larnaca", "Paphos", "Famagusta", 
        "Kyrenia", "Protaras", "Ayia Napa", "Paralimni", "Morphou"
    ],
    "Czechia": [
        "Prague", "Brno", "Ostrava", "Pilsen", "Liberec", 
        "Olomouc", "Ceske Budejovice", "Hradec Kralove", "Usti nad Labem", "Pardubice", "Zlin"
    ],
    # --- D ---
    "Democratic Republic of the Congo": [
        "Kinshasa", "Lubumbashi", "Mbuji-Mayi", "Kananga", "Kisangani",
        "Bukavu", "Tshikapa", "Kolwezi", "Likasi", "Goma", "Kikwit", "Uvira"
    ],
    "Denmark": [
        "Copenhagen", "Aarhus", "Odense", "Aalborg", "Esbjerg",
        "Randers", "Kolding", "Horsens", "Vejle", "Roskilde", "Herning"
    ],
    "Djibouti": [
        "Djibouti City", "Ali Sabieh", "Tadjoura", "Obock", "Dikhil",
        "Arta", "Holhol", "Dorra", "Randa", "Loyada"
    ],
    "Dominica": [
        "Roseau", "Portsmouth", "Marigot", "Berekua", "Mahaut",
        "Saint Joseph", "Canefield", "Wesley", "Salisbury", "Castle Bruce"
    ],
    "Dominican Republic": [
        "Santo Domingo", "Santiago de los Caballeros", "Los Alcarrizos", "La Romana", "San Pedro de Macoris",
        "Higuey", "San Cristobal", "Puerto Plata", "San Francisco de Macoris", "Concepcion de la Vega"
    ],

    # --- E ---
    "Ecuador": [
        "Guayaquil", "Quito", "Cuenca", "Santo Domingo", "Machala",
        "Duran", "Manta", "Portoviejo", "Loja", "Ambato", "Esmeraldas", "Riobamba"
    ],
    "Egypt": [
        "Cairo", "Alexandria", "Giza", "Shubra El Kheima", "Port Said",
        "Suez", "Luxor", "Mansoura", "El-Mahalla El-Kubra", "Tanta",
        "Asyut", "Ismailia", "Faiyum", "Zagazig", "Aswan",
        "Damietta", "Damanhur", "Minya", "Beni Suef", "Qena",
        "Sohag", "Hurghada", "6th of October City", "Shibin El Kom", "Banha",
        "Kafr el-Sheikh", "Arish", "Mallawi", "10th of Ramadan City", "Bilbais", "Sharm El Sheikh"
    ],
    "El Salvador": [
        "San Salvador", "Soyapango", "Santa Ana", "San Miguel", "Mejicanos",
        "Apopa", "Delgado", "Santa Tecla", "Ilopango", "Colon"
    ],
    "Equatorial Guinea": [
        "Bata", "Malabo", "Ebebiyin", "Aconibe", "Anisoc",
        "Luba", "Evinayong", "Mongomo", "Mengomeyen", "Ciudad de la Paz"
    ],
    "Eritrea": [
        "Asmara", "Keren", "Massawa", "Assab", "Mendefera",
        "Barentu", "Adi Keyh", "Adi Quala", "Dekemhare", "Ak'ordat"
    ],
    "Estonia": [
        "Tallinn", "Tartu", "Narva", "Parnu", "Kohtla-Jarve",
        "Viljandi", "Rakvere", "Maardu", "Kuressaare", "Sillamae"
    ],
    "Eswatini": [
        "Manzini", "Mbabane", "Big Bend", "Malkerns", "Nhlangano",
        "Mhlume", "Hluti", "Simunye", "Siteki", "Piggs Peak"
    ],
    "Ethiopia": [
        "Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Adama",
        "Hawassa", "Bahir Dar", "Jimma", "Dessie", "Jijiga",
        "Shashamane", "Bishoftu", "Sodo", "Arba Minch", "Hosaena",
        "Harar", "Dilla", "Nekemte", "Debre Birhan", "Asella",
        "Debre Mark'os", "Kombolcha", "Debre Tabor", "Adigrat", "Weldiya",
        "Sebeta", "Burayu", "Shire", "Ambo", "Arsi Negele"
    ],

    # --- F ---
    "Fiji": [
        "Suva", "Lautoka", "Nadi", "Labasa", "Ba",
        "Nausori", "Sigatoka", "Savusavu", "Levuka", "Tavua"
    ],
    "Finland": [
        "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu",
        "Turku", "Jyvaskyla", "Lahti", "Kuopio", "Pori", "Kouvola", "Joensuu"
    ],
    "France": [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
        "Nantes", "Montpellier", "Strasbourg", "Bordeaux", "Lille",
        "Rennes", "Reims", "Saint-Etienne", "Toulon", "Le Havre",
        "Grenoble", "Dijon", "Angers", "Nimes", "Villeurbanne",
        "Clermont-Ferrand", "Le Mans", "Aix-en-Provence", "Brest", "Tours",
        "Amiens", "Limoges", "Annecy", "Perpignan", "Boulogne-Billancourt",
        "Metz", "Besancon", "Orleans", "Rouen", "Cannes"
    ],

    # --- G ---
    "Gabon": [
        "Libreville", "Port-Gentil", "Franceville", "Oyem", "Moanda",
        "Mouila", "Lambarene", "Tchibanga", "Koulamoutou", "Makokou"
    ],
    "Gambia": [
        "Serekunda", "Brikama", "Bakau", "Banjul", "Farafenni",
        "Lamin", "Nema Kunku", "Brufut", "Sukuta", "Basse Santa Su"
    ],
    "Georgia": [
        "Tbilisi", "Batumi", "Kutaisi", "Rustavi", "Gori",
        "Zugdidi", "Poti", "Khashuri", "Samtredia", "Senaki"
    ],
    "Germany": [
        "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt",
        "Stuttgart", "Dusseldorf", "Leipzig", "Dortmund", "Essen",
        "Bremen", "Dresden", "Hanover", "Nuremberg", "Duisburg",
        "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Munster",
        "Mannheim", "Karlsruhe", "Augsburg", "Wiesbaden", "Monchengladbach",
        "Gelsenkirchen", "Aachen", "Braunschweig", "Chemnitz", "Kiel",
        "Halle", "Magdeburg", "Freiburg", "Krefeld", "Mainz", "Bavaria"
    ],
    "Ghana": [
        "Accra", "Kumasi", "Tamale", "Sekondi-Takoradi", "Ashaiman",
        "Sunyani", "Cape Coast", "Obuasi", "Teshie", "Tema", "Koforidua"
    ],
    "Greece": [
        "Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa",
        "Volos", "Rhodes", "Ioannina", "Chania", "Chalcis", "Alexandroupoli"
    ],
    "Grenada": [
        "St. George's", "Gouyave", "Grenville", "Victoria", "St. David's",
        "Sauteurs", "Hillsborough", "Grand Roy", "Woburn", "Marquis"
    ],
    "Guatemala": [
        "Guatemala City", "Mixco", "Villa Nueva", "Quetzaltenango", "San Miguel Petapa",
        "Escuintla", "San Juan Sacatepequez", "Villa Canales", "Chinautla", "Chimaltenango"
    ],
    "Guinea": [
        "Conakry", "Nzerekore", "Kankan", "Kindia", "Siguiri",
        "Boke", "Kissidougou", "Labe", "Dubréka", "Kamsar"
    ],
    "Guinea-Bissau": [
        "Bissau", "Bafata", "Gabu", "Bissora", "Bolama",
        "Cacheu", "Bubaque", "Catio", "Mansoa", "Buba"
    ],
    "Guyana": [
        "Georgetown", "Linden", "New Amsterdam", "Anna Regina", "Bartica",
        "Skeldon", "Rosignol", "Mahaica", "Parika", "Vreed-en-Hoop"
    ],

    # --- H ---
    "Haiti": [
        "Port-au-Prince", "Carrefour", "Delmas", "Petion-Ville", "Gonaives",
        "Cap-Haitien", "Saint-Marc", "Verrettes", "Les Cayes", "Jacmel"
    ],
    "Holy See": [
        "Vatican City", "Saint Peter's Square", "Vatican Gardens", "Borgo", "Castel Gandolfo",
        "Lateran", "Apostolic Palace", "Sistine Chapel", "Vatican Hill", "Leonine City"
    ],
    "Honduras": [
        "Tegucigalpa", "San Pedro Sula", "Choloma", "La Ceiba", "El Progreso",
        "Choluteca", "Comayagua", "Puerto Cortes", "La Lima", "Danli"
    ],
    "Hungary": [
        "Budapest", "Debrecen", "Szeged", "Miskolc", "Pecs",
        "Gyor", "Nyiregyhaza", "Kecskemet", "Szekesfehervar", "Szombathely"
    ],

    # --- I ---
    "Iceland": [
        "Reykjavik", "Kopavogur", "Hafnarfjordur", "Reykjanesbaer", "Akureyri",
        "Gardabaer", "Mosfellsbaer", "Arborg", "Akranes", "Fjardabyggd"
    ],
    "India": [
        "Mumbai", "Delhi", "New Delhi", "Bangalore", "Bengaluru",
        "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Surat",
        "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
        "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad",
        "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra",
        "Nashik", "Faridabad", "Meerut", "Rajkot", "Varanasi",
        "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai",
        "Prayagraj", "Ranchi", "Howrah", "Coimbatore", "Guwahati", "Chandigarh"
    ],
    "Indonesia": [
        "Jakarta", "Surabaya", "Bekasi", "Bandung", "Medan",
        "Depok", "Tangerang", "Palembang", "Semarang", "Makassar",
        "South Tangerang", "Batam", "Bandar Lampung", "Bogor", "Pekanbaru",
        "Padang", "Malang", "Samarinda", "Denpasar", "Tasikmalaya",
        "Serang", "Balikpapan", "Pontianak", "Banjarmasin", "Jambi",
        "Surakarta", "Cimahi", "Manado", "Kupang", "Jayapura", "Yogyakarta"
    ],
    "Iran": [
        "Tehran", "Mashhad", "Isfahan", "Karaj", "Shiraz",
        "Tabriz", "Qom", "Ahvaz", "Kermanshah", "Urmia",
        "Rasht", "Zahedan", "Hamadan", "Kerman", "Yazd",
        "Ardabil", "Bandar Abbas", "Arak", "Eslamshahr", "Zanjan",
        "Sanandaj", "Qazvin", "Khorramabad", "Gorgan", "Sari",
        "Shahriar", "Qods", "Kashan", "Malard", "Dezful", "Abadan"
    ],
    "Iraq": [
        "Baghdad", "Basra", "Mosul", "Erbil", "Abu Ghraib",
        "Sulaymaniyah", "Kirkuk", "Najaf", "Karbala", "Nasiriyah",
        "Amarah", "Diwaniyah", "Kut", "Hillah", "Duhok", "Ramadi", "Fallujah"
    ],
    "Ireland": [
        "Dublin", "Cork", "Limerick", "Galway", "Waterford",
        "Drogheda", "Swords", "Dundalk", "Bray", "Navan", "Kilkenny", "Ennis"
    ],
    "Israel": [
        "Jerusalem", "Tel Aviv", "Haifa", "Rishon LeZion", "Petah Tikva",
        "Ashdod", "Netanya", "Beersheba", "Bnei Brak", "Holon",
        "Ramat Gan", "Rehovot", "Ashkelon", "Bat Yam", "Beit Shemesh",
        "Kfar Saba", "Herzliya", "Hadera", "Modiin", "Nazareth",
        "Lod", "Ramla", "Ra'anana", "Rahat", "Givatayim",
        "Hod HaSharon", "Kiryat Ata", "Nahariya", "Eilat", "Tiberias"
    ],
    "Italy": [
        "Rome", "Milan", "Naples", "Turin", "Palermo",
        "Genoa", "Bologna", "Florence", "Bari", "Catania",
        "Venice", "Verona", "Messina", "Padua", "Trieste",
        "Brescia", "Parma", "Taranto", "Prato", "Modena",
        "Reggio Calabria", "Reggio Emilia", "Perugia", "Ravenna", "Livorno",
        "Cagliari", "Foggia", "Rimini", "Salerno", "Ferrara", "Sicily", "Sardinia"
    ],
    "Ivory Coast": [
        "Abidjan", "Bouake", "Daloa", "Yamoussoukro", "Korhogo",
        "San-Pedro", "Gagnoa", "Divo", "Anyama"
    ],

    # --- J ---
    "Jamaica": [
        "Kingston", "Portmore", "Spanish Town", "Montego Bay", "May Pen",
        "Mandeville", "Old Harbour", "Savanna-la-Mar", "Ocho Rios", "Linstead"
    ],
    "Japan": [
        "Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo",
        "Fukuoka", "Kobe", "Kawasaki", "Kyoto", "Saitama",
        "Hiroshima", "Sendai", "Chiba", "Kitakyushu", "Sakai",
        "Niigata", "Hamamatsu", "Kumamoto", "Sagamihara", "Okayama",
        "Shizuoka", "Funabashi", "Kagoshima", "Kawaguchi", "Hachioji",
        "Himeji", "Matsuyama", "Utsunomiya", "Higashiosaka", "Nara", "Okinawa"
    ],
    "Jordan": [
        "Amman", "Zarqa", "Irbid", "Russeifa", "Sahab",
        "Ar Ramtha", "Aqaba", "Mafraq", "Madaba", "As-Salt", "Jerash"
    ],

    # --- K ---
    "Kazakhstan": [
        "Almaty", "Astana", "Shymkent", "Aktobe", "Karaganda",
        "Taraz", "Pavlodar", "Ust-Kamenogorsk", "Semey", "Atyrau", "Kostanay", "Kyzylorda"
    ],
    "Kenya": [
        "Nairobi", "Mombasa", "Nakuru", "Ruiru", "Eldoret",
        "Kisumu", "Kikuyu", "Ngong", "Mavoko", "Thika", "Naivasha", "Malindi"
    ],
    "Kiribati": [
        "Tarawa", "Betio", "Bikenibeu", "Teaoraereke", "Bairiki",
        "Eita", "Bonriki", "Temwaiku", "Taburao"
    ],
    "Kuwait": [
        "Kuwait City", "Al Ahmadi", "Hawalli", "As Salimiyah", "Sabah as Salim",
        "Al Farwaniyah", "Al Fahahil", "Ar Riqqah", "Al Manqaf", "Al Jahra"
    ],
    "Kyrgyzstan": [
        "Bishkek", "Osh", "Jalal-Abad", "Karakol", "Tokmok",
        "Uzgen", "Balykchy", "Kara-Balta", "Naryn", "Talas"
    ],

    # --- L ---
    "Laos": [
        "Vientiane", "Pakse", "Savannakhet", "Luang Prabang", "Xam Neua",
        "Phonsavan", "Thakhek", "Muang Xay", "Vang Vieng", "Luang Namtha"
    ],
    "Latvia": [
        "Riga", "Daugavpils", "Liepaja", "Jelgava", "Jurmala",
        "Ventspils", "Rezekne", "Valmiera", "Jekabpils", "Ogre"
    ],
    "Lebanon": [
        "Beirut", "Tripoli", "Sidon", "Tyre", "Nabatieh",
        "Jounieh", "Zahle", "Baalbek", "Byblos", "Batroun"
    ],
    "Lesotho": [
        "Maseru", "Teyateyaneng", "Mafeteng", "Hlotse", "Mohale's Hoek",
        "Maputsoe", "Qacha's Nek", "Quthing", "Butha-Buthe", "Mokhotlong"
    ],
    "Liberia": [
        "Monrovia", "Gbarnga", "Kakata", "Bensonville", "Harper",
        "Voinjama", "Buchanan", "Zwedru", "New Yekepa", "Greenville"
    ],
    "Libya": [
        "Tripoli", "Benghazi", "Misrata", "Bayda", "Zawiya",
        "Zliten", "Tobruk", "Ajdabiya", "Sabha", "Derna", "Sirte"
    ],
    "Liechtenstein": [
        "Schaan", "Vaduz", "Triesen", "Balzers", "Eschen",
        "Mauren", "Triesenberg", "Ruggell", "Gamprin", "Schellenberg"
    ],
    "Lithuania": [
        "Vilnius", "Kaunas", "Klaipeda", "Siauliai", "Panevezys",
        "Alytus", "Marijampole", "Mazeikiai", "Jonava", "Utena"
    ],
    "Luxembourg": [
        "Luxembourg City", "Esch-sur-Alzette", "Differdange", "Dudelange", "Ettelbruck",
        "Diekirch", "Wiltz", "Echternach", "Rumelange", "Grevenmacher"
    ],

    # --- M ---
    "Madagascar": [
        "Antananarivo", "Toamasina", "Antsirabe", "Mahajanga", "Fianarantsoa",
        "Toliara", "Antsiranana", "Ambovombe", "Amparafaravola", "Tolagnaro"
    ],
    "Malawi": [
        "Lilongwe", "Blantyre", "Mzuzu", "Zomba", "Kasungu",
        "Mangochi", "Karonga", "Salima", "Nkhotakota", "Liwonde"
    ],
    "Malaysia": [
        "Kuala Lumpur", "George Town", "Ipoh", "Shah Alam", "Petaling Jaya",
        "Johor Bahru", "Malacca City", "Kota Kinabalu", "Alor Setar", "Kuala Terengganu",
        "Kuching", "Seremban", "Kuantan", "Subang Jaya", "Klang",
        "Kajang", "Selayang", "Ampang Jaya", "Sandakan", "Tawau",
        "Miri", "Sibu", "Bintulu", "Putrajaya", "Cyberjaya",
        "Kota Bharu", "Sungai Petani", "Kulim", "Taiping", "Batu Pahat", "Penang"
    ],
    "Maldives": [
        "Male", "Addu City", "Fuvahmulah", "Kulhudhuffushi", "Thinadhoo",
        "Naifaru", "Hithadhoo", "Dhidhdhoo", "Eydhafushi", "Mahibadhoo"
    ],
    "Mali": [
        "Bamako", "Sikasso", "Kalabancoro", "Koutiala", "Segou",
        "Kayes", "Kati", "Mopti", "Niono", "Gao", "Timbuktu"
    ],
    "Malta": [
        "Birkirkara", "Mosta", "St. Paul's Bay", "Qormi", "Zabbar",
        "Sliema", "Naxxar", "San Gwann", "Zebbug", "Valletta", "Mdina"
    ],
    "Marshall Islands": [
        "Majuro", "Ebeye", "Arno", "Jabor", "Wotje",
        "Mili", "Kili", "Bikini", "Kwajalein", "Rongelap"
    ],
    "Mauritania": [
        "Nouakchott", "Nouadhibou", "Nema", "Kaedi", "Rosso",
        "Kiffa", "Zouerat", "Atar", "Selibaby", "Aleg"
    ],
    "Mauritius": [
        "Port Louis", "Beau Bassin-Rose Hill", "Vacoas-Phoenix", "Curepipe", "Quatre Bornes",
        "Triolet", "Goodlands", "Centre de Flacq", "Bel Air", "Mahebourg"
    ],
    "Mexico": [
        "Mexico City", "Tijuana", "Ecatepec", "Leon", "Puebla",
        "Ciudad Juarez", "Guadalajara", "Zapopan", "Monterrey", "Nezahualcoyotl",
        "Chihuahua", "Merida", "Naucalpan", "Toluca", "Cancun",
        "Saltillo", "Aguascalientes", "Hermosillo", "Mexicali", "San Luis Potosi",
        "Culiacan", "Queretaro", "Morelia", "Chimalhuacan", "Reynosa",
        "Torreon", "Tlalnepantla", "Acapulco", "Tlaquepaque", "Guadalupe", "Oaxaca"
    ],
    "Micronesia": [
        "Weno", "Palikir", "Tofol", "Colonia", "Nett",
        "Kitti", "Madolenihmw", "Sokehs", "Uh", "Tol"
    ],
    "Moldova": [
        "Chisinau", "Tiraspol", "Balti", "Bender", "Ribnita",
        "Ungheni", "Cahul", "Soroca", "Orhei", "Comrat"
    ],
    "Monaco": [
        "Monte Carlo", "La Condamine", "Fontvieille", "Monaco-Ville", "Moneghetti",
        "Larvotto", "La Rousse", "Saint-Michel", "La Colle", "Les Revoires"
    ],
    "Mongolia": [
        "Ulaanbaatar", "Erdenet", "Darkhan", "Choibalsan", "Murun",
        "Nalaikh", "Bayankhongor", "Olgiy", "Khovd", "Arvaikheer"
    ],
    "Montenegro": [
        "Podgorica", "Niksic", "Herceg Novi", "Pljevlja", "Bar",
        "Bijelo Polje", "Cetinje", "Budva", "Kotor", "Berane", "Ulcinj"
    ],
    "Morocco": [
        "Casablanca", "Fez", "Tangier", "Marrakech", "Sale",
        "Meknes", "Rabat", "Oujda", "Kenitra", "Agadir",
        "Tetouan", "Temara", "Safi", "Mohammedia", "Khouribga",
        "El Jadida", "Beni Mellal", "Ait Melloul", "Nador", "Dar Bouazza",
        "Taza", "Settat", "Berrechid", "Khemisset", "Inezgane",
        "Ksar El Kebir", "Larache", "Guelmim", "Khenifra", "Berkane"
    ],
    "Mozambique": [
        "Maputo", "Matola", "Nampula", "Beira", "Chimoio",
        "Nacala", "Quelimane", "Tete", "Lichinga", "Pemba", "Xai-Xai"
    ],
    "Myanmar": [
        "Yangon", "Mandalay", "Naypyidaw", "Mawlamyine", "Bago",
        "Pathein", "Monywa", "Sittwe", "Meiktila", "Myeik", "Taunggyi"
    ],

    # --- N ---
    "Namibia": [
        "Windhoek", "Rundu", "Walvis Bay", "Swakopmund", "Oshakati",
        "Rehoboth", "Katima Mulilo", "Otjiwarongo", "Okahandja", "Ondangwa"
    ],
    "Nauru": [
        "Yaren", "Denigomodu", "Meneng", "Aiwo", "Boe",
        "Anabar", "Ijuw", "Anibare", "Uaboe", "Nibok"
    ],
    "Nepal": [
        "Kathmandu", "Pokhara", "Lalitpur", "Bharatpur", "Biratnagar",
        "Birgunj", "Janakpur", "Ghorahi", "Hetauda", "Dhangadhi", "Butwal", "Dharan"
    ],
    "Netherlands": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen",
        "Apeldoorn", "Haarlem", "Arnhem", "Enschede", "Amersfoort",
        "Zaanstad", "Haarlemmermeer", "Zwolle", "Zoetermeer", "Leiden",
        "Maastricht", "Dordrecht", "Ede", "Alphen aan den Rijn", "Westland",
        "Alkmaar", "Emmen", "Delft", "Venlo", "Deventer", "Leeuwarden"
    ],
    "New Zealand": [
        "Auckland", "Wellington", "Christchurch", "Tauranga",
        "Lower Hutt", "Dunedin", "Palmerston North", "Napier", "Hibiscus Coast",
        "Porirua", "New Plymouth", "Rotorua", "Whangarei", "Nelson", "Invercargill"
    ],
    "Nicaragua": [
        "Managua", "Leon", "Masaya", "Matagalpa", "Tipitapa",
        "Chinandega", "Jinotega", "Esteli", "Granada", "Ciudad Sandino"
    ],
    "Niger": [
        "Niamey", "Zinder", "Maradi", "Agadez", "Tahoua",
        "Dosso", "Birni-N'Konni", "Tessaoua", "Gaya", "Diffa"
    ],
    "Nigeria": [
        "Lagos", "Kano", "Ibadan", "Benin City", "Port Harcourt",
        "Jos", "Ilorin", "Abuja", "Kaduna", "Enugu",
        "Zaria", "Warri", "Ikorodu", "Maiduguri", "Aba",
        "Ife", "Bauchi", "Akure", "Abeokuta", "Oyo",
        "Uyo", "Sokoto", "Owerri", "Yola", "Calabar",
        "Umuahia", "Ondo", "Minna", "Lafia", "Okene", "Onitsha"
    ],
    "North Korea": [
        "Pyongyang", "Hamhung", "Chongjin", "Nampo", "Wonsan",
        "Sinuiju", "Tanchon", "Kaechon", "Kaesong", "Sariwon", "Hyesan"
    ],
    "North Macedonia": [
        "Skopje", "Bitola", "Kumanovo", "Prilep", "Tetovo",
        "Veles", "Stip", "Ohrid", "Gostivar", "Strumica"
    ],
    "Norway": [
        "Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen",
        "Fredrikstad", "Kristiansand", "Sandnes", "Tromso", "Sarpsborg", "Skien", "Alesund"
    ],

    # --- O ---
    "Oman": [
        "Muscat", "Seeb", "Salalah", "Bawshar", "Sohar",
        "As Suwayq", "Ibri", "Saham", "Barka", "Rustaq", "Nizwa"
    ],

    # --- P ---
    "Pakistan": [
        "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Gujranwala",
        "Peshawar", "Multan", "Hyderabad", "Islamabad", "Quetta",
        "Bahawalpur", "Sargodha", "Sialkot", "Sukkur", "Larkana",
        "Sheikhupura", "Rahim Yar Khan", "Jhang", "Dera Ghazi Khan", "Gujrat",
        "Sahiwal", "Wah Cantonment", "Mardan", "Kasur", "Okara",
        "Mingora", "Nawabshah", "Chiniot", "Kotri", "Kamoke",
        "Hafizabad", "Sadiqabad", "Mirpur Khas", "Burewala", "Kohat",
        "Abbottabad", "Muzaffarabad", "Gilgit", "Gwadar", "Imran Khan"
    ],
    "Palau": [
        "Koror", "Airai", "Kloulklubed", "Meyuns", "Ngerulmud",
        "Ulimang", "Ngarchelong", "Ngardmau", "Aimeliik", "Melekeok"
    ],
    "Palestine": [
        "Gaza City", "East Jerusalem", "Hebron", "Nablus", "Rafah",
        "Khan Yunis", "Jabalia", "Ramallah", "Bethlehem", "Tulkarm", "Jenin", "Jericho"
    ],
    "Panama": [
        "Panama City", "San Miguelito", "Tocumen", "David", "Arraijan",
        "Colon", "Las Cumbres", "La Chorrera", "Pacora", "Santiago"
    ],
    "Papua New Guinea": [
        "Port Moresby", "Lae", "Arawa", "Mount Hagen", "Popondetta",
        "Madang", "Kokopo", "Mendi", "Kimbe", "Goroka", "Panguna", "Bougainville"
    ],
    "Paraguay": [
        "Asuncion", "Ciudad del Este", "San Lorenzo", "Luque", "Capiata",
        "Lambare", "Fernando de la Mora", "Limpio", "Nemby", "Encarnacion"
    ],
    "Peru": [
        "Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura",
        "Iquitos", "Cusco", "Chimbote", "Huancayo", "Tacna",
        "Juliaca", "Ica", "Cajamarca", "Pucallpa", "Sullana",
        "Ayacucho", "Chincha Alta", "Huanuco", "Huacho", "Tarapoto",
        "Puno", "Paita", "Huaraz", "Tumbes", "Talara",
        "Huaral", "Pisco", "Chulucanas", "Moquegua", "Cerro de Pasco"
    ],
    "Philippines": [
        "Quezon City", "Manila", "Davao City", "Caloocan", "Cebu City",
        "Zamboanga City", "Taguig", "Antipolo", "Pasig", "Cagayan de Oro",
        "Paranaque", "Dasmarinas", "Valenzuela", "Bacoor", "General Santos",
        "Las Pinas", "Makati", "San Jose del Monte", "Bacolod", "Muntinlupa",
        "Calamba", "Marikina", "Iloilo City", "Pasay", "Angeles",
        "Lapu-Lapu", "Imus", "Mandaluyong", "Malabon", "Mandaue", "Baguio"
    ],
    "Poland": [
        "Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan",
        "Gdansk", "Szczecin", "Bydgoszcz", "Lublin", "Bialystok",
        "Katowice", "Gdynia", "Czestochowa", "Radom", "Torun",
        "Sosnowiec", "Rzeszow", "Kielce", "Gliwice", "Olsztyn",
        "Zabrze", "Bielsko-Biala", "Bytom", "Zielona Gora", "Rybnik",
        "Ruda Slaska", "Opole", "Tychy", "Gorzow Wielkopolski", "Elblag"
    ],
    "Portugal": [
        "Lisbon", "Porto", "Vila Nova de Gaia", "Amadora", "Braga",
        "Funchal", "Coimbra", "Setubal", "Almada", "Agualva-Cacem", "Queluz", "Faro"
    ],

    # --- Q ---
    "Qatar": [
        "Doha", "Al Rayyan", "Umm Salal Muhammad", "Al Wakrah", "Al Khor",
        "Al Shamal", "Dukhan", "Mesaieed", "Lusail", "Al Shahaniya"
    ],

    # --- R ---
    "Romania": [
        "Bucharest", "Cluj-Napoca", "Timisoara", "Iasi", "Constanta",
        "Craiova", "Brasov", "Galati", "Ploiesti", "Oradea",
        "Braila", "Arad", "Pitesti", "Sibiu", "Bacau",
        "Targu Mures", "Baia Mare", "Buzau", "Botosani", "Satu Mare",
        "Ramnicu Valcea", "Drobeta-Turnu Severin", "Suceava", "Piatra Neamt", "Targu Jiu",
        "Targoviste", "Focsani", "Bistrita", "Tulcea", "Resita"
    ],
    "Russia": [
        "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan",
        "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov-on-Don",
        "Ufa", "Krasnoyarsk", "Voronezh", "Perm", "Volgograd",
        "Krasnodar", "Saratov", "Tyumen", "Tolyatti", "Izhevsk",
        "Barnaul", "Ulyanovsk", "Irkutsk", "Khabarovsk", "Yaroslavl",
        "Vladivostok", "Makhachkala", "Tomsk", "Orenburg", "Kemerovo",
        "Novokuznetsk", "Ryazan", "Astrakhan", "Naberezhnye Chelny", "Sochi", "Kaliningrad"
    ],
    "Rwanda": [
        "Kigali", "Gisenyi", "Ruhengeri", "Butare", "Muhanga",
        "Byumba", "Cyangugu", "Nyanza", "Rwamagana", "Kibungo"
    ],

    # --- S ---
    "Saint Kitts and Nevis": [
        "Basseterre", "Charlestown", "Sadlers", "Cayon", "Mansion",
        "Sandy Point Town", "Gingerland", "Newcastle", "Dieppe Bay Town", "Old Road Town"
    ],
    "Saint Lucia": [
        "Castries", "Bisee", "Vieux Fort", "Micoud", "Soufriere",
        "Dennery", "Gros Islet", "Anse La Raye", "Canaries", "Choiseul"
    ],
    "Saint Vincent and the Grenadines": [
        "Kingstown", "Georgetown", "Byera Village", "Biabou", "Port Elizabeth",
        "Chateaubelair", "Barrouallie", "Layou", "Calliaqua", "Mesopotamia"
    ],
    "Samoa": [
        "Apia", "Vaitele", "Faleula", "Siusega", "Malie",
        "Fasito'o Uta", "Vaiusu", "Satapuala", "Salelologa", "Afega"
    ],
    "San Marino": [
        "Serravalle", "Borgo Maggiore", "San Marino", "Domagnano", "Fiorentino",
        "Acquaviva", "Faetano", "Chiesanuova", "Montegiardino", "Dogana"
    ],
    "Sao Tome and Principe": [
        "Sao Tome", "Santo Amaro", "Neves", "Santana", "Trindade",
        "Santa Cruz", "Pantufo", "Guadalupe", "Santo Antonio", "Ribeira Afonso"
    ],
    "Saudi Arabia": [
        "Riyadh", "Jeddah", "Mecca", "Medina", "Hofuf",
        "Taif", "Dammam", "Khobar", "Buraydah", "Tabuk",
        "Qatif", "Khamis Mushait", "Ha'il", "Hafar Al-Batin", "Jubail",
        "Al-Kharj", "Abha", "Najran", "Yanbu", "Al Qunfudhah",
        "Dhahran", "Arar", "Sakaka", "Jizan", "Qurayyat",
        "Al Bahah", "Tarout", "Bisha", "Unaizah", "Ras Tanura", "NEOM"
    ],
    "Senegal": [
        "Dakar", "Pikine", "Touba", "Guediawaye", "Thies",
        "Kaolack", "M'Bour", "Saint-Louis", "Rufisque", "Ziguinchor"
    ],
    "Serbia": [
        "Belgrade", "Novi Sad", "Nis", "Kragujevac", "Subotica",
        "Zrenjanin", "Pancevo", "Cacak", "Kraljevo", "Novi Pazar", "Smederevo"
    ],
    "Seychelles": [
        "Victoria", "Anse Boileau", "Bel Ombre", "Beau Vallon", "Cascade",
        "Takamaka", "Port Glaud", "Anse Royale", "Grand Anse", "Baie Lazare"
    ],
    "Sierra Leone": [
        "Freetown", "Bo", "Kenema", "Makeni", "Koidu",
        "Lunsar", "Port Loko", "Waterloo", "Kabala", "Segbwema"
    ],
    "Singapore": [
        "Singapore", "Jurong West", "Woodlands", "Tampines", "Sengkang",
        "Hougang", "Yishun", "Bedok", "Punggol", "Ang Mo Kio", "Bukit Merah", "Changi"
    ],
    "Slovakia": [
        "Bratislava", "Kosice", "Presov", "Zilina", "Banska Bystrica",
        "Nitra", "Trnava", "Trencin", "Martin", "Poprad"
    ],
    "Slovenia": [
        "Ljubljana", "Maribor", "Celje", "Kranj", "Koper",
        "Velenje", "Novo Mesto", "Ptuj", "Trbovlje", "Kamnik"
    ],
    "Solomon Islands": [
        "Honiara", "Auki", "Gizo", "Buala", "Tulagi",
        "Kirakira", "Lata", "Taro Island", "Noro", "Munda"
    ],
    "Somalia": [
        "Mogadishu", "Hargeisa", "Bosaso", "Galkayo", "Berbera",
        "Merca", "Jamaame", "Kismayo", "Baidoa", "Burao", "Beledweyne"
    ],
    "South Africa": [
        "Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth",
        "Gqeberha", "Bloemfontein", "Nelspruit", "Mbombela", "Kimberley",
        "Polokwane", "Pietermaritzburg", "East London", "Rustenburg", "Welkom",
        "Vereeniging", "Tembisa", "Soweto", "Benoni", "Boksburg",
        "Krugersdorp", "Botshabelo", "Brakpan", "Richards Bay", "Witbank",
        "Potchefstroom", "Vanderbijlpark", "Centurion", "Uitenhage", "George", "Stellenbosch"
    ],
    "South Korea": [
        "Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
        "Gwangju", "Suwon", "Ulsan", "Changwon", "Goyang",
        "Yongin", "Seongnam", "Bucheon", "Cheongju", "Ansan",
        "Jeonju", "Cheonan", "Namyangju", "Hwaseong", "Anyang",
        "Gimhae", "Pohang", "Pyeongtaek", "Jeju", "Siheung",
        "Uijeongbu", "Gumi", "Paju", "Gimpo", "Jinju"
    ],
    "South Sudan": [
        "Juba", "Winejok", "Malakal", "Wau", "Pajok",
        "Yei", "Yambio", "Aweil", "Gogrial", "Rumbek", "Bor"
    ],
    "Spain": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
        "Malaga", "Murcia", "Palma", "Las Palmas", "Bilbao",
        "Alicante", "Cordoba", "Valladolid", "Vigo", "Gijon",
        "Hospitalet de Llobregat", "Vitoria-Gasteiz", "A Coruna", "Elche", "Granada",
        "Terrassa", "Badalona", "Oviedo", "Sabadell", "Cartagena",
        "Jerez de la Frontera", "Mostoles", "Santa Cruz de Tenerife", "Pamplona", "Almeria", "Catalonia"
    ],
    "Sri Lanka": [
        "Colombo", "Dehiwala-Mount Lavinia", "Moratuwa", "Sri Jayawardenepura Kotte", "Negombo",
        "Kandy", "Kalmunai", "Vavuniya", "Galle", "Trincomalee", "Batticaloa", "Jaffna"
    ],
    "Sudan": [
        "Omdurman", "Khartoum", "Khartoum North", "Nyala", "Port Sudan",
        "Kassala", "El-Obeid", "Kosti", "Wad Madani", "El Fasher", "Gedaref"
    ],
    "Suriname": [
        "Paramaribo", "Lelydorp", "Brokopondo", "Nieuw Nickerie", "Moengo",
        "Nieuw Amsterdam", "Marienburg", "Wageningen", "Albina", "Groningen"
    ],
    "Sweden": [
        "Stockholm", "Gothenburg", "Malmo", "Uppsala", "Upplands Vasby",
        "Vasteras", "Orebro", "Linkoping", "Helsingborg", "Jonkoping",
        "Norrkoping", "Lund", "Umea", "Gavle", "Boras",
        "Sodertalje", "Eskilstuna", "Halmstad", "Vaxjo", "Karlstad",
        "Sundsvall", "Ostersund", "Trollhattan", "Lulea", "Nordmaling",
        "Taby", "Kalmar", "Falun", "Skelleftea", "Kristianstad"
    ],
    "Switzerland": [
        "Zurich", "Geneva", "Basel", "Lausanne", "Bern",
        "Winterthur", "Lucerne", "St. Gallen", "Lugano", "Biel/Bienne",
        "Thun", "Bellinzona", "Koniz", "Fribourg", "Schaffhausen",
        "Chur", "Vernier", "Neuchatel", "Uster", "Sion",
        "Lancy", "Yverdon-les-Bains", "Emmen", "Zug", "Kriens",
        "Rapperswil-Jona", "Dubendorf", "Montreux", "Dietikon", "Frauenfeld", "Davos"
    ],
    "Syria": [
        "Aleppo", "Damascus", "Homs", "Latakia", "Hama",
        "Raqqa", "Deir ez-Zor", "Al-Hasakah", "Qamishli", "Idlib", "Tartus", "Daraa"
    ],

    # --- T ---
    "Taiwan": [
        "New Taipei", "Taichung", "Kaohsiung", "Taipei", "Taoyuan",
        "Tainan", "Hsinchu", "Keelung", "Chiayi", "Changhua",
        "Pingtung", "Zhubei", "Yuanlin", "Douliu", "Taitung",
        "Hualien", "Nantou", "Yilan", "Miaoli", "Magong",
        "Toufen", "Lukang", "Caotun", "Fengyuan", "Dali",
        "Taiping", "Zhongli", "Banqiao", "Sanchong", "Zhonghe"
    ],
    "Tajikistan": [
        "Dushanbe", "Khujand", "Bokhtar", "Kulob", "Istaravshan",
        "Vahdat", "Konibodom", "Tursunzoda", "Isfara", "Panjakent"
    ],
    "Tanzania": [
        "Dar es Salaam", "Mwanza", "Arusha", "Dodoma", "Mbeya",
        "Morogoro", "Tanga", "Kahama", "Tabora", "Zanzibar City", "Kigoma"
    ],
    "Thailand": [
        "Bangkok", "Nonthaburi", "Nakhon Ratchasima", "Chiang Mai", "Hat Yai",
        "Udon Thani", "Pak Kret", "Khon Kaen", "Chaophraya Surasak", "Ubon Ratchathani",
        "Nakhon Si Thammarat", "Nakhon Sawan", "Nakhon Pathom", "Phitsanulok", "Pattaya",
        "Songkhla", "Surat Thani", "Rangsit", "Yala", "Phuket",
        "Samut Prakan", "Lampang", "Laem Chabang", "Chiang Rai", "Trang",
        "Phra Nakhon Si Ayutthaya", "Ko Samui", "Samut Sakhon", "Rayong", "Mae Sot"
    ],
    "Timor-Leste": [
        "Dili", "Dare", "Lospalos", "Baucau", "Maliana",
        "Suai", "Liquica", "Same", "Aileu", "Viqueque"
    ],
    "Togo": [
        "Lome", "Sokode", "Kara", "Kpalime", "Atakpame",
        "Bassar", "Tsevie", "Aneho", "Mango", "Dapaong"
    ],
    "Tonga": [
        "Nuku'alofa", "Neiafu", "Haveluloto", "Vaini", "Pangai",
        "Ohonua", "Hihifo", "Tofoa", "Kolonga", "Houma"
    ],
    "Trinidad and Tobago": [
        "Chaguanas", "San Fernando", "Port of Spain", "Arima", "Marabella",
        "Point Fortin", "Tunapuna", "Scarborough", "Sangre Grande", "Penal"
    ],
    "Tunisia": [
        "Tunis", "Sfax", "Sousse", "Ettadhamen", "Kairouan",
        "Gabes", "Bizerte", "Aryanah", "Gafsa", "El Mourouj", "Monastir"
    ],
    "Turkey": [
        "Istanbul", "Ankara", "Izmir", "Bursa", "Adana",
        "Gaziantep", "Konya", "Antalya", "Kayseri", "Mersin",
        "Eskisehir", "Diyarbakir", "Samsun", "Denizli", "Sanliurfa",
        "Adapazari", "Malatya", "Kahramanmaras", "Erzurum",
        "Batman", "Elazig", "Izmit", "Manisa", "Sivas",
        "Gebze", "Balikesir", "Tarsus", "Kutahya", "Trabzon", "Bodrum"
    ],
    "Turkmenistan": [
        "Ashgabat", "Turkmenabat", "Dasoguz", "Mary", "Balkanabat",
        "Bayramaly", "Turkmenbashi", "Tejen", "Abadan", "Magdanly"
    ],
    "Tuvalu": [
        "Funafuti", "Savave", "Tanrake", "Toga", "Asau",
        "Kulia", "Fakaifou", "Senala", "Alapi", "Vaiaku"
    ],

    # --- U ---
    "Uganda": [
        "Kampala", "Nansana", "Kira", "Ssabagabo", "Mbarara",
        "Mukono", "Gulu", "Lugazi", "Masaka", "Kasese", "Jinja", "Entebbe"
    ],
    "Ukraine": [
        "Kyiv", "Kiev", "Kharkiv", "Odesa", "Odessa",
        "Dnipro", "Donetsk", "Zaporizhzhia", "Lviv", "Kryvyi Rih",
        "Mykolaiv", "Mariupol", "Luhansk", "Vinnytsia", "Makiivka",
        "Sevastopol", "Simferopol", "Kherson", "Poltava", "Chernihiv",
        "Cherkasy", "Khmelnytskyi", "Chernivtsi", "Zhytomyr", "Sumy",
        "Rivne", "Horlivka", "Ivano-Frankivsk", "Kamianske", "Ternopil",
        "Kropyvnytskyi", "Kremenchuk", "Lutsk", "Crimea", "Donbas"
    ],
    "United Arab Emirates": [
        "Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Ajman",
        "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Khor Fakkan", "Kalba",
        "Jebel Ali", "Dibba Al-Fujairah", "Madinat Zayed", "Ruwais", "Liwa Oasis",
        "Dhaid", "Ghayathi", "Ar-Rams", "Dibba Al-Hisn", "Hatta",
        "Al Madam", "Masafi", "Al Jazirah Al Hamra", "Sweihan", "Al Mirfa",
        "Sila", "Delma Island", "Sir Bani Yas", "Al Dhaid", "Mussafah"
    ],
    "United Kingdom": [
        "London", "Birmingham", "Manchester", "Glasgow", "Newcastle",
        "Sheffield", "Liverpool", "Leeds", "Bristol", "Edinburgh",
        "Leicester", "Coventry", "Bradford", "Cardiff", "Belfast",
        "Nottingham", "Kingston upon Hull", "Stoke-on-Trent", "Wolverhampton", "Derby",
        "Swansea", "Southampton", "Salford", "Aberdeen", "Westminster",
        "Portsmouth", "Peterborough", "Dundee", "Lancaster",
        "Oxford", "Cambridge", "Brighton", "Plymouth", "Scotland", "Wales", "Northern Ireland"
    ],
    "United States": [
        "New York", "New York City", "NYC", "Los Angeles", "Chicago",
        "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego",
        "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth",
        "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle",
        "Denver", "Washington", "Washington D.C.", "Boston", "El Paso",
        "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas",
        "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque",
        "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta",
        "Miami", "Oakland", "Minneapolis", "Cleveland", "New Orleans",
        "California", "Texas", "Florida", "Delaware", "Silicon Valley", "Wall Street", "Donald Trump","Trump","White House","FAA", "Silicon Valley","Hollywood"
    ],
    "Uruguay": [
        "Montevideo", "Salto", "Ciudad de la Costa", "Paysandu", "Las Piedras",
        "Rivera", "Maldonado", "Tacuarembo", "Melo", "Mercedes", "Punta del Este"
    ],
    "Uzbekistan": [
        "Tashkent", "Namangan", "Samarkand", "Andijan", "Nukus",
        "Bukhara", "Qarshi", "Kokand", "Fergana", "Margilan", "Urgench", "Khiva"
    ],

    # --- V ---
    "Vanuatu": [
        "Port Vila", "Luganville", "Norsup", "Port-Olry", "Isangel",
        "Sola", "Lakatoro", "Saratamata", "Longana", "Lenakel"
    ],
    "Venezuela": [
        "Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay",
        "Ciudad Guayana", "Barcelona", "Maturin", "Petare", "Turmero",
        "Ciudad Bolivar", "Barinas", "Los Teques", "Cumana", "San Cristobal",
        "Cabimas", "Merida", "Puerto La Cruz", "Guarenas", "Punto Fijo",
        "Acarigua", "Carupano", "El Tigre", "Guatire", "Coro",
        "Valera", "Cabudare", "Puerto Cabello", "Anaco", "Calabozo"
    ],
    "Vietnam": [
        "Ho Chi Minh City", "Saigon", "Hanoi", "Da Nang", "Haiphong",
        "Bien Hoa", "Can Tho", "Thuan An", "Di An", "Hue",
        "Vung Tau", "Thu Dau Mot", "Nha Trang", "Quy Nhon", "Long Xuyen",
        "Thai Nguyen", "Buon Ma Thuot", "Rach Gia", "Vinh", "Da Lat",
        "Ha Long", "Nam Dinh", "Phan Thiet", "Thanh Hoa", "My Tho",
        "Thai Binh", "Cam Ranh", "Bac Ninh", "Pleiku", "Ca Mau"
    ],

    # --- Y ---
    "Yemen": [
        "Sanaa", "Aden", "Taiz", "Al Hudaydah", "Ibb",
        "Dhamar", "Mukalla", "Zinjibar", "Sayyan", "Ash Shihr", "Marib", "Socotra"
    ],

    # --- Z ---
    "Zambia": [
        "Lusaka", "Kitwe", "Ndola", "Kabwe", "Chingola",
        "Mufulira", "Livingstone", "Luanshya", "Kasama", "Chipata"
    ],
    "Zimbabwe": [
        "Harare", "Bulawayo", "Chitungwiza", "Mutare", "Epworth",
        "Gweru", "Kwekwe", "Kadoma", "Masvingo", "Chinhoyi", "Victoria Falls"
    ],
}


# These short/common names are too ambiguous to match on their own.
# Their longer official names and less ambiguous demonyms remain usable.
AMBIGUOUS_ALIASES = {
    "america",
    "car",
    "congo",
    "congolese",
    "dominican",
    "dominicans",
    "georgia",
    "jordan",
    "korea",
    "korean",
    "turkey",
}


# ============================================================
# 3. TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize text so accented and unaccented spellings can match.

    Examples:
        Türkiye -> turkiye
        Côte d'Ivoire -> cote d'ivoire
    """

    if value is None:
        return ""

    text = str(value).casefold()
    text = unicodedata.normalize("NFKD", text)

    # Remove accent marks.
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    # Normalize apostrophes and dashes.
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[‐‑‒–—]", "-", text)

    return text


# ============================================================
# 4. COMPILE COUNTRY NAME ALIASES
# ============================================================

COMPILED_ALIASES = []

for country, aliases in COUNTRY_ALIASES.items():

    for alias in aliases:

        normalized_alias = normalize_text(alias)

        if not normalized_alias:
            continue

        if normalized_alias in AMBIGUOUS_ALIASES:
            continue

        pattern = re.compile(
            r"(?<![\w])"
            + re.escape(normalized_alias)
            + r"(?![\w])"
        )

        COMPILED_ALIASES.append((country, pattern))


# ============================================================
# 5. COMPILE COUNTRY CODES
# ============================================================

COMPILED_CODES = []

for country, codes in CODE_ALIASES.items():

    for code in codes:

        pattern = re.compile(
            r"(?<![A-Za-z0-9])"
            + re.escape(code)
            + r"(?![A-Za-z0-9])"
        )

        COMPILED_CODES.append((country, pattern))


# ============================================================
# 6. COMPILE CITY AND LOCATION ALIASES
# ============================================================

COMPILED_CITIES = []

for country, aliases in CITY_ALIASES.items():

    for alias in aliases:

        normalized_alias = normalize_text(alias)

        if not normalized_alias:
            continue

        # Allow spaces or hyphens between words.
        alias_pattern = re.escape(normalized_alias).replace(
            r"\ ", r"[\s-]+"
        )

        pattern = re.compile(
            r"(?<![\w])" + alias_pattern + r"(?![\w])"
        )

        COMPILED_CITIES.append((country, pattern))


# ============================================================
# 7. COUNTRY RECOGNITION FUNCTION
# ============================================================

def find_countries(text):
    """
    Detect countries through:
    1. Country names and demonyms
    2. Uppercase country codes
    3. Selected cities and locations

    This is rule-based headline recognition.
    It does not understand context or identify the main actor.
    """

    if not isinstance(text, str) or not text.strip():
        return []

    normalized_text = normalize_text(text)

    detected_countries = set()

    # --------------------------------------------------------
    # 1. Match country names and demonyms
    # --------------------------------------------------------

    for country, pattern in COMPILED_ALIASES:

        if pattern.search(normalized_text):
            detected_countries.add(country)

    # --------------------------------------------------------
    # 2. Match uppercase country codes
    # --------------------------------------------------------

    for country, pattern in COMPILED_CODES:

        for match in pattern.finditer(text):

            # Avoid interpreting US$ as the United States.
            if (
                country == "United States"
                and match.group(0) == "US"
                and text[match.end():].startswith("$")
            ):
                continue

            detected_countries.add(country)

    # --------------------------------------------------------
    # 3. Match cities and selected locations
    # --------------------------------------------------------

    for country, pattern in COMPILED_CITIES:

        if pattern.search(normalized_text):
            detected_countries.add(country)

    # --------------------------------------------------------
    # 4. Return results in COUNTRY_ALIASES order
    # --------------------------------------------------------

    return [
        country
        for country in COUNTRY_ALIASES
        if country in detected_countries
    ]


# ============================================================
# 8. LOAD CLEANED DATASET
# ============================================================

def main():

    print("\nLoading cleaned news dataset...")

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    required_columns = [
        "source",
        "title",
        "published",
        "link"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print(f"Total articles loaded: {len(df)}")

    # Recognition is currently based on headlines only.
    detected = df["title"].apply(find_countries)

    df["countries"] = detected.apply(
        lambda countries: (
            ", ".join(countries)
            if countries
            else "Unknown"
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # ========================================================
    # 9. DISPLAY RECOGNITION REPORT
    # ========================================================

    detected_count = (
        df["countries"] != "Unknown"
    ).sum()

    unknown_count = len(df) - detected_count

    print("\n========== STATECRAFT MONITOR ==========")
    print("       COUNTRY RECOGNITION REPORT")
    print("========================================")

    print(f"Total articles processed: {len(df)}")
    print(f"Articles with detected entities: {detected_count}")
    print(f"Articles without detected entities: {unknown_count}")

    print("\nDetected entities:")

    entity_counts = (
        detected.explode()
        .dropna()
        .value_counts()
    )

    if entity_counts.empty:

        print("No country/entity mentions detected.")

    else:

        print(entity_counts.to_string())

    print("\nArticle-level results:")

    for _, article in df.iterrows():

        print(f"\nHeadline: {article['title']}")
        print(f"Detected entities: {article['countries']}")
        print("-" * 65)

    print(f"\nEnriched dataset saved at:\n{OUTPUT_FILE}")

    print("\n========================================")


# ============================================================
# 10. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()
