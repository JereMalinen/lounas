# This Python file uses the following encoding: utf-8
import urllib
from datetime import datetime
import shutil
import re
import logging


DAYS = ('Maanantai', 'Tiistai', 'Keskiviikko', 'Torstai', 'Perjantai')
DAY_ABBREVIATONS = ('Ma', 'Ti', 'Ke', 'To', 'Pe') #for karppaklubi

DAY_HOLDER = '<DAY>'

path = './'

start = datetime.now()


class LunchPage(object):
    filename = path + 'lounas.html'

    def __init__(self):
        upseerikerho = Restaurant(name='Upseerikerho', 
                                  url='http://www3.luovi.fi/Ravintola_Upseerikerho/Lounaslista',
                                  regex='(?P<lunch><p><strong>(.{0,10})' + DAY_HOLDER + '(.*?)</table>)')
        little_new_york = Restaurant(name='Little New York', 
                                     url='http://www.ravintolalittlenewyork.fi/3',
                                     regex='(?P<day>^(.*)' + DAY_HOLDER + '(.*?)\n)(?P<lunch>^(.*?)Tilauksesta(.*?)\n)',
                                     encoding='ISO-8859-1')
        indian_cuisine = Restaurant(name='Indian Cuisine', 
                                    url='http://www.indiancuisine.fi/menu_lunch/lunchmenu.htm',
                                    regex='(?P<day><h2(.{0,20}))' + DAY_HOLDER + '(.*?)(?P<lunch><table>(.*?)</table>)')
        rehapolis = Restaurant(name='Rehapolis', 
                               url='http://www.uniresta.fi/uniresta.php?ruokalista=13',
                               regex='(?P<lunch><span(.{0,20})' + DAY_HOLDER + '(.{20,1000}?))<br /><br />',
                               encoding='ISO-8859-1')
        karppa = Restaurant(name=smart_str('Kärppäklubi'),
                               url='http://www.karppaklubi.fi/sivu.php?sivu=3',
                               regex='(?P<lunch><b>' + DAY_HOLDER + '(.{20,200}?))<br><br>',
                               encoding='ISO-8859-1',
                               abbreviations=True)
        kantis = Restaurant(name='Kantis', 
                               url='http://www.kantis.net/lounas.php',
                               regex='(?P<lunch><span(.{0,20})' + DAY_HOLDER + '(.*?)</span>)',
                               encoding='ISO-8859-1',
                               multipage=['http://www.kantis.net/lounas.php?id=1',
                                          'http://www.kantis.net/lounas.php?id=2',
                                          'http://www.kantis.net/lounas.php?id=3',
                                          'http://www.kantis.net/lounas.php?id=4',
                                          'http://www.kantis.net/lounas.php?id=5',])
        oskari = Restaurant(name='Oskarin Kellari', 
                               url='http://www.oskarinkellari.com',
                               regex='(?P<lunch><TABLE border=0 cellpadding=2(.*?)</TABLE>)',
                               encoding='ISO-8859-1',
                               multipage=['http://www.oskarinkellari.com/docs/templates/app_lunch.php3?page_id=11',
                                          'http://www.oskarinkellari.com/docs/templates/app_lunch.php3?page_id=12',
                                          'http://www.oskarinkellari.com/docs/templates/app_lunch.php3?page_id=13',
                                          'http://www.oskarinkellari.com/docs/templates/app_lunch.php3?page_id=14',
                                          'http://www.oskarinkellari.com/docs/templates/app_lunch.php3?page_id=15',])
        
        restaurants = [upseerikerho, rehapolis, little_new_york, kantis, indian_cuisine, oskari]
        self.restaurants = []
        for restaurant in restaurants:
            try:
                logger.info("Parsing " + restaurant.name)
                restaurant.parse_lunch()
                self.restaurants.append(restaurant)
            except Exception, ex:    
                logger.exception(restaurant.name + " failed!")
                
    def write(self):
        f = open(LunchPage.filename, 'w')
        f.write('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>Oulun lounaita</title></head>\n')
        f.write('<body style="background-color: #E7E7E7;">\n')
        f.write('<h1>Oulun lounaita</h1>\n')
        f.write(smart_str('<p>Päivitetty: ' + start.strftime('%d.%m.%Y %H:%M') + ' (viikko: ' + start.strftime('%W') + ')</p>\n'))
        f.write('<div>\n')
        for day in DAYS:
            f.write('<a href="#' + day + '">' + day + '</a>\n')
        f.write('</div>\n')
        f.write('<br />')
        f.write('<div><table style="background-color: #F8FFBF; border: solid 1px;">\n')
        f.write('<tr><th> </th>\n')
        for restaurant in self.restaurants:
            f.write('<th style="background-color: #9BCFAF; border: solid 1px;"><a href="' + restaurant.url + '">' + restaurant.name + '</a></th>\n')
        f.write('</tr>\n')
        for day in DAYS:
            f.write('<tr><th style="background-color: #BFE2FF; border: solid 1px;" id="' + day + '">')
            for letter in day:
                f.write(letter.upper() + '<br />')
            f.write('</th>\n')
            for restaurant in self.restaurants:
                    f.write('<td style="background-color: white; border: solid 1px;">' + smart_str(restaurant.daily_lunch[day]) + '</td>\n')
            f.write('</tr>\n')
        f.write('</table></div>\n')
        f.write('<p><a href="arkisto/">Arkisto</a></p>\n')
        time = datetime.now() - start
        f.write('<p>Sivun generointi kesti noin ' + str(time.seconds) + '.' + str(time.microseconds * 1000) + ' sekuntia</p>')
        f.write(smart_str('<p>(Tämän sivun tiedot eivät välttämättä ole aina oikein.)</p>'))
        f.write('</body></html>\n')
        f.close()
        
    def copy_archive(self):
        arcive_file = path + 'arkisto/lounas_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.html'
        logger.info('Copying file to archive file: ' + arcive_file)
        shutil.copyfile(LunchPage.filename, arcive_file)


class Restaurant(object):
    def __init__(self, name='', url='', regex='', encoding='utf-8', multipage=[], abbreviations=False):
        self.name = name
        self.url = url
        self.regex = regex
        self.encoding = encoding
        self.multipage = multipage
        self.abbreviations = abbreviations
        self.daily_lunch = {}
        
    def parse_lunch(self):
        if self.multipage and self.regex:
            self.parse_multi_page()
        elif self.regex:
            self.parse_single_page()
        else:
            logger.warning('No parser for: ' + self.url)

    def parse_single_page(self):
        sock = urllib.urlopen(self.url)
        page = sock.read()
        sock.close()
        #print chardet.detect(page)['encoding']
        if not abbreviations:
            d = DAYS
        else:
            d = DAY_ABBREVIATONS
        for day in d:
            m = re.search(self.regex.replace(DAY_HOLDER, day), page, re.I|re.S|re.M)
            if m:
                logger.debug(m.group('lunch'))
                self.daily_lunch[day] = unicode(m.group('lunch'), encoding=self.encoding)
            else:
                logger.error('Parser did not work: ' + self.name + ' ' + day)
                self.daily_lunch[day] = '???'
                
    def parse_multi_page(self):
        for i, url in enumerate(self.multipage):
            sock = urllib.urlopen(url)
            page = sock.read()
            sock.close()
            #print DAYS[i]
            m = re.search(self.regex.replace(DAY_HOLDER, DAYS[i]), page, re.I|re.S|re.M)
            if m:
                logger.debug(m.group('lunch'))
                self.daily_lunch[DAYS[i]] = unicode(m.group('lunch'), encoding=self.encoding)
                self.daily_lunch[DAYS[i]] = self.daily_lunch[DAYS[i]].replace('width=115', '')
            else:
                logger.error('Parser did not work: ' + self.name + ' ' + url)
                self.daily_lunch[DAYS[i]] = '???'
                


def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (None, int)):
        return s
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

LOG_LEVEL = logging.INFO
logger = logging.getLogger('lounas.py')
logger.setLevel(LOG_LEVEL)
ch = logging.StreamHandler()
ch_file = logging.FileHandler(filename='lounas.log')
ch.setLevel(logging.ERROR)
ch_file.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
ch_file.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(ch_file)

logger.info('Generating...')
try:
    lunchpage = LunchPage()
    lunchpage.write()
    lunchpage.copy_archive()
except Exception, ex:
    logger.exception("Something awful happened!")
