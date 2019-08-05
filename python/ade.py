from requests import Session
from lxml import html
from cours import CM, TP
from slot import Slot
from datetime import datetime, timedelta
from warnings import warn
from static_data import Q2_START, Q1, Q2, Q3
from professor import Professor


def getCoursesFromCodes(course_tags, weeks, projectID=2):
    """ Fetches courses schedule from UCLouvain ADE website
    Parameters:
    -----------
    courses : list of str
    weeks : list of int
    projectID : int
    """

    # some variables
    q = [week < Q2_START for week in weeks]
    nb_weeks = len(weeks)
    entry = ['date', 'tag', 'time', 'duration', 'name', 'teacher', 'mail', 'room']
    cm_added = []
    tp_added = []
    cm_list = []
    tp_list = []

    # generating the URL for ADE
    url = 'http://horaire.uclouvain.be/jsp/custom/modules/plannings/direct_planning.jsp?'
    opt = '&showTab=true&showTabInstructors=true&showImage=true&iE=true&displayConfId=46&display=true&x=&y=&isClickable' \
          '=true&changeOptions=true&displayType=0&showLoad=false&showTreeCategory2=true&showTabActivity=true&showTabWeek' \
          '=false&showTabDay=false&showTabStage=false&showTabDate=true&showTabHour=true&showTabDuration=true&aC=true&aTy' \
          '=false&aUrl=false&aSize=false&aMx=false&aSl=false&aCx=false&aCy=false&aCz=false&aTz=false&aN=false&aNe=false' \
          '&showTabTrainees=false&sC=false&sTy=false&sUrl=false&sE=false&sM=false&sJ=false&sA1=false&sA2=false&sZp=false' \
          '&sCi=false&sSt=false&sCt=false&sT=false&sF=false&sCx=false&sCy=false&sCz=false&sTz=false&showTabRooms=true&roC' \
          '=false&roTy=false&roUrl=false&roE=false&roM=false&roJ=false&roA1=false&roA2=false&roZp=false&roCi=false&roSt' \
          '=false&roCt=false&roT=false&roF=false&roCx=false&roCy=false&roCz=false&roTz=false&showTabResources=false&reC' \
          '=false&reTy=false&reUrl=false&reE=false&reM=false&reJ=false&reA1=false&reA2=false&reZp=false&reCi=false&reSt' \
          '=false&reCt=false&reT=false&reF=false&reCx=false&reCy=false&reCz=false&reTz=false&showTabCategory5=false&c5C' \
          '=false&c5Ty=false&c5Url=false&c5E=false&c5M=false&c5J=false&c5A1=false&c5A2=false&c5Zp=false&c5Ci=false&c5St' \
          '=false&c5Ct=false&c5T=false&c5F=false&c5Cx=false&c5Cy=false&c5Cz=false&c5Tz=false&showTabCategory6=false&c6C' \
          '=false&c6Ty=false&c6Url=false&c6E=false&c6M=false&c6J=false&c6A1=false&c6A2=false&c6Zp=false&c6Ci=false&c6St' \
          '=false&c6Ct=false&c6T=false&c6F=false&c6Cx=false&c6Cy=false&c6Cz=false&c6Tz=false&showTabCategory7=false&c7C' \
          '=false&c7Ty=false&c7Url=false&c7E=false&c7M=false&c7J=false&c7A1=false&c7A2=false&c7Zp=false&c7Ci=false&c7St' \
          '=false&c7Ct=false&c7T=false&c7F=false&c7Cx=false&c7Cy=false&c7Cz=false&c7Tz=false&showTabCategory8=false&c8C' \
          '=false&c8Ty=false&c8Url=false&c8E=false&c8M=false&c8J=false&c8A1=false&c8A2=false&c8Zp=false&c8Ci=false&c8St' \
          '=false&c8Ct=false&c8T=false&c8F=false&c8Cx=false&c8Cy=false&c8Cz=false&c8Tz=false '
    codes = '%2C'.join(course_tags)
    weeks = ','.join(str(x) for x in weeks)
    url += '&weeks=' + weeks \
           + '&code=' + codes \
           + '&login=etudiant&password=student&projectId=' + str(projectID) \
           + opt

    # fetching data from ADE
    s = Session()
    r = s.get(url)
    r = s.get('http://horaire.uclouvain.be/jsp/custom/modules/plannings/info.jsp?order=slot&amp;clearTree=false')
    s.close()
    tree = html.fromstring(r.content)
    data = tree.xpath('//tr')[2:]  # the two first lines are titles


    # constructing the course list
    for i, line in enumerate(data):
        c = {}
        el = line.iterchildren()
        for y in entry:
            c[y] = str(next(el).text_content())

        tdebut = datetime.strptime(c['date'] + '-' + c['time'], '%d/%m/%Y-%Hh%M')
        h, m = [0 if x is '' else int(x) for x in c['duration'].split('h')]
        dt = timedelta(hours=h, minutes=m)
        tfin = tdebut + dt
        if '-' in c['tag']:  # CM
            if '_' in c['tag']:
                warn('Both - and _ found in course tag, assuming it is a CM.')
            tag = c['tag'].split('-')[0]
            iscm = True
        else:
            tag = c['tag'].split('_')[0]
            iscm = False

        try:  # The course was already added, we just add the corresponding time slot
            if iscm:
                i = cm_added.index(tag)
                cm_list[i].add_slot(Slot(tdebut, tfin))
            else:
                i = tp_added.index(tag)
                tp_list[i].add_slot(Slot(tdebut, tfin))

        except ValueError:  # This is a new course
            pr = Professor(c['teacher'], c['mail'])
            if iscm:    # CM
                cm_added.append(tag)
                cm_list.append(CM(c['name'], tag, pr, nb_weeks=nb_weeks, Q=q[i]))
                cm_list[-1].add_slot(Slot(tdebut, tfin))
            else:   # TP
                tp_added.append(tag)
                tp_list.append(TP(c['name'], tag, pr, nb_weeks=nb_weeks, Q=q[i]))
                tp_list[-1].add_slot(Slot(tdebut, tfin))

    return cm_list, tp_list


_, _ = getCoursesFromCodes(['lepl1102'], Q1+Q2+Q3)