# module for working with XML
from lxml import etree
import lxml.html as lhtml
# # module for arguments
# module to sort out html entities
import html
# work with times
from datetime import date, time

# for getting files form urls
import urllib.request
import urllib.error
import ssl
# module for regex
import re


# clean up text and tail text on element and all decendents
def clean_up_text(element):
    for element in element.iterdescendants():
        if element.text:
            element.text = dumb_to_smart_quotes(
                remove_no_break_spaces_etc(element.text))
        if element.tail:
            element.tail = dumb_to_smart_quotes(
                remove_no_break_spaces_etc(element.tail))


def dumb_to_smart_quotes(string):
    """Takes a string and returns it with dumb quotes, single and double,
        replaced by smart quotes."""

    # LEFT DOUBLE QUOTATION MARK  \u201C
    # RIGHT DOUBLE QUOTATION MARK  \u201D

    # RIGHT SINGLE QUOTATION MARK \u2019
    # LEFT SINGLE QUOTATION MARK  \u2018

    # opening quotes
    # quotes after space and before letter or number or opening paren
    string = re.sub(r' "([a-zA-Z0-9(])', ' \u201C\\1', string)  # double
    string = re.sub(r" '([a-zA-Z0-9(])", ' \u2018\\1', string)  # single
    # quote at beginning of string
    string = re.sub(r'^"([a-zA-Z0-9(])', '\u201C\\1', string)  # double
    string = re.sub(r"^'([a-zA-Z0-9(])", '\u2018\\1', string)  # single

    # closing quotes
    # quote after letter and before space or one of `.?,!)`
    string = re.sub(r'([a-zA-Z.?,!)])"([\s.?,!)])', '\\1\u201D\\2', string)  # double
    string = re.sub(r"([a-zA-Z.?,!)])'([\s.?,!)])", '\\1\u2019\\2', string)  # single
    # quote at end of string
    string = re.sub(r'([a-zA-Z.?,!)])"$', '\\1\u201D', string)  # double
    string = re.sub(r"([a-zA-Z.?,!)])'$", '\\1\u2019', string)  # single

    # appostraphy
    string = re.sub(r"([a-zA-Z])'([a-zA-Z])", '\\1\u2019\\2', string)

    return string


def remove_no_break_spaces_etc(string):
    # need to remove unnessesary line breaks and non breaking spaces
    string = re.sub(r'\n\n+', '\n', string)
    # remove some of the non breaking spaces followed by line break
    string = re.sub(r'\u00A0\n\u00A0\n+', '\u00A0\n', string)
    # remove all of the non breaking spaces
    string = re.sub(r'\u00A0+', ' ', string)

    return string


def get_mnis_data(laying_minister_lookup):

    # this will contain key value pairs.
    # member ID -> laying minister name
    laying_minister_lookup = {}

    # the MNIS url where the data is stored
    url = 'http://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons|IsEligible=true'
    # ignore the ssl certificate
    context = ssl._create_unverified_context()

    print('\nGetting Laying Minister names from,\n{}'.format(url))
    try:
        response = urllib.request.urlopen(url, context=context)
    except urllib.error.HTTPError as e:
        # 404 and other HTTP errors will be caught here.
        print('WARNING: There is a error in getting the laying ministers names from MNIS\n' +
              '\tCheck the following URL is working, {}\n'.format(url) +
              '\t{}'.format(e))  # actually output the error
    else:
        print('Got the data.')
        mnis_root = etree.parse(response).getroot()
        # check if the returned element has children. If not warn the user.
        if len(mnis_root) == 0:
            print(
                'WARNING: It looks like there is a problem with the laying ministers data, check {}'.format(url)
            )
        print('\nThe following member names will be replaced by their Laying Minister name when sponsoring motions or ammendments:')
        print('  Member Name:\t\t    Laying Minister Name:')
        for member_element in mnis_root:
            Member_Id          = member_element.get('Member_Id')
            LayingMinisterName = member_element.findtext('LayingMinisterName', default='')
            member_name        = member_element.findtext('DisplayAs', default='')
            if LayingMinisterName != '':
                laying_minister_lookup[Member_Id] = LayingMinisterName
                if member_name != LayingMinisterName:
                    if len(member_name) <= 13:
                        print('  {}\t\t->  {}'.format(member_name, LayingMinisterName))
                    else:
                        print('  {}\t->  {}'.format(member_name, LayingMinisterName))
        # newline
        print()

    return laying_minister_lookup


def notes_relevant_docs(dayItem, output_root, has_children, day_item_is_child):
    if has_children is False:
        # get any notes
        notes = dayItem.findtext('BusinessItemDetail/Notes')
        if notes is not None and notes.strip() != '':
            append_fromstring(
                output_root,
                '<NoteHeading>Notes:&#8233;</NoteHeading>'
            )
            append_fromstring(
                output_root,
                '<NoteText>' + notes + '&#8233;</NoteText>'
            )
        relevant_documents = dayItem.findtext('BusinessItemDetail/RelevantDocuments')
        if relevant_documents is not None and relevant_documents.strip() != '':
            append_fromstring(
                output_root,
                '<NoteHeading>Relevant Documents:&#8233;</NoteHeading>'
            )
            append_fromstring(
                output_root,
                '<NoteText>' + relevant_documents + '&#8233;</NoteText>'
            )
    # get notes and Relavant documents for parent item if last child
    if dayItem.getnext() is None and day_item_is_child is True:
        # get any notes
        notes = dayItem.getparent().getparent().findtext('Notes')
        if notes is not None and notes.strip() != '':
            append_fromstring(
                output_root,
                '<NoteHeading>Notes:&#8233;</NoteHeading>'
            )
            append_fromstring(
                output_root,
                '<NoteText>' + notes + '&#8233;</NoteText>'
            )
        relevant_documents = dayItem.getparent().getparent().findtext('RelevantDocuments')
        if relevant_documents is not None and relevant_documents.strip() != '':
            append_fromstring(
                output_root,
                '<NoteHeading>Relevant Documents:&#8233;</NoteHeading>'
            )
            append_fromstring(
                output_root,
                '<NoteText>' + relevant_documents + '&#8233;</NoteText>'
            )


def append_timing_so(output_root, current_element):
    duration_text = current_element.findtext('BusinessItemDetail/Duration', default='')
    so_text       = current_element.findtext('BusinessItemDetail/StandingOrders/StandingOrder/Text', default='')
    if (duration_text != '' and so_text != ''):
        append_fromstring(
            output_root,
            '<DebateTimingRubric>' +
            duration_text + ' ' +
            '<SOReference>(' + so_text +
            ')</SOReference>' +
            '&#8233;</DebateTimingRubric>'
        )
    elif duration_text != '':
        append_fromstring(
            output_root,
            '<DebateTimingRubric>' + duration_text +
            '&#8233;</DebateTimingRubric>'
        )
    elif so_text != '':
        append_fromstring(
            output_root,
            '<DebateTimingRubric><SOReference>(' + so_text +
            ')</SOReference>&#8233;</DebateTimingRubric>'
        )


def append_ammendments(dayItem, append_to, laying_minister_lookup):
    # make sure we get any amendments
    amendments = dayItem.findall('BusinessItemDetail/Amendments/Amendment')
    previous_amendment_letter = ''
    for amendment in amendments:
        # add the amendment leter text e.g. Amednment (a)
        amendment_letter = next_letter(previous_amendment_letter)
        append_fromstring(
            append_to,
            '<MotionAmmendmentSponsor>Amendment(' + amendment_letter + ')&#8233;</MotionAmmendmentSponsor>'
        )
        previous_amendment_letter = amendment_letter
        # print(amendment[0].text)
        sponsors = amendment.find('Sponsors')
        # first 6 sponsors are in bold and each on one line
        if len(sponsors) > 0:
            for sponsor in sponsors[:6]:
                sponsor_name = sponsor.findtext('Name', default='').strip()
                member_id = sponsor.findtext('MemberId', default='')
                # replace sponsor if they have a laying minister name
                # e.g. Mrs Theresa May -> The Prime Minister
                if member_id in laying_minister_lookup:
                    sponsor_name = laying_minister_lookup[member_id]
                append_fromstring(
                    append_to,
                    '<MotionAmmendmentSponsor>' + sponsor_name + '&#8233;</MotionAmmendmentSponsor>'
                )
        # after the first 6 sponsors are not in bold and 3 per line
        if len(sponsors) > 6:
            m_a_s_g = etree.Element('MotionAmmendmentSponsorGroup')
            m_a_s_g.text = ''
            for next_sponsor in sponsors[6:]:
                m_a_s_g.text += next_sponsor.findtext('Name', default='') + '\t'
            m_a_s_g.text += '\n'
            append_to.append(m_a_s_g)
        append_fromstring(
            append_to,
            '<MotionAmmendmentText>' +
            amendment.findtext('FriendlyDescription', default='').strip() +
            '&#8233;</MotionAmmendmentText>'
        )


def append_presenter_sponsor(dayItem, append_to):
    # we dont need to include a laying_minister_lookup because
    # gov cant sponsor any items that take a presentor sponsor
    # this is a presentor sponsor and there can only be one of thoes
    sponsor = dayItem.find('BusinessItemDetail/Sponsors/Sponsor')
    if sponsor is not None:
        sponsor_name = sponsor.findtext('Name', default='')
        relevant_interest = ''
        if sponsor.findtext('HasRelevantInterest') == 'true':
            relevant_interest = ' [R]'
        append_fromstring(
            append_to,
            '<PresenterSponsor>' + sponsor_name + relevant_interest + '&#8233;</PresenterSponsor>'
        )


def by_sort_order(sponsor_element):
    sort_order = sponsor_element.findtext('SortOrder')
    try:
        return int(sort_order)
    except ValueError:
        return sort_order


def append_motion_sponosrs(dayItem, append_to, laying_minister_lookup):
    sponsors = dayItem.find('BusinessItemDetail/Sponsors')
    # motion ammendment sponsor group
    m_a_s_g = etree.Element('MotionSponsorGroup')
    m_a_s_g.text = ''
    sponsors = sorted(sponsors, key=by_sort_order)
    for i, sponsor in enumerate(sponsors):
        sponsor_name = sponsor.findtext('Name', default='')
        member_id = sponsor.findtext('MemberId', default='')
        # replace sponsor if they have a laying minister name
        # e.g. Mrs Theresa May -> The Prime Minister
        if member_id in laying_minister_lookup:
            sponsor_name = laying_minister_lookup[member_id]
        sponsor_notes = dayItem.findtext('BusinessItemDetail/SponsorNotes')
        if i == 0 and (sponsor_notes is not None and sponsor_notes.strip() != ''):
            sponosr_note_xml = ', <SponsorNotes>{}</SponsorNotes>'.format(sponsor_notes)
        else:
            sponosr_note_xml = ''

        # first 6 sponsors are in bold and each on one line
        if i == 0:
            append_fromstring(
                append_to,
                '<MotionSponsor>{}{}&#8233;</MotionSponsor>'
                .format(sponsor_name, sponosr_note_xml)
            )
        elif i > 0 and i < 6:
            append_fromstring(
                append_to,
                '<MotionSponsor>' + sponsor_name.strip() +
                '&#8233;</MotionSponsor>'
            )
        # after the first 6 sponsors are not in bold and 3 per line
        else:
            m_a_s_g.text += sponsor_name + '\t'
    if len(sponsors) > 6:
            m_a_s_g.tail = '\u2029'  # will map to &#8233; paragraph sep
            append_to.append(m_a_s_g)


def append_fromstring(parent, xml_string):
    xml_string = html.unescape(xml_string).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
    xml_string = re.sub(r'&([^#])', '&amp; ', xml_string)
    parent.append(etree.fromstring(xml_string))


def process_CDATA(text_from_xml):
    unescaped = html.unescape(text_from_xml).strip()
    cdata_element_string = '<from_cdata>' + unescaped + '</from_cdata>'
    # create an lxml html element
    cdata_element = lhtml.fromstring(cdata_element_string)

    # ---- TABLES -----------------

    # create a number for the max width of the table
    max_table_width = 466  # this is measured in points

    # get all the table elements
    tables = cdata_element.xpath('//table')
    # go through the tables backwards because there could be tables in tables...
    for table in reversed(tables):
        table_rows = table.xpath('tbody/tr|thead/tr|tfoot/tr|tr')
        # number of table rows
        table_rows_number = len(table_rows)
        # now find out the maximum number of cells in each row
        max_cells = 0
        for row in table_rows:
            table_cells = row.xpath('td|th')
            number_of_cells = len(table_cells)
            if number_of_cells > max_cells:
                max_cells = number_of_cells
        # create InDesign table element
        inDesign_tabel = etree.fromstring('<Table xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" xmlns:aid5="http://ns.adobe.com/AdobeInDesign/5.0/" aid:table="table" aid5:tablestyle="StandardTable"></Table>')
        # fix rows and colls attributes
        inDesign_tabel.set('{http://ns.adobe.com/AdobeInDesign/4.0/}tcols', str(max_cells))
        inDesign_tabel.set('{http://ns.adobe.com/AdobeInDesign/4.0/}trows', str(table_rows_number))
        # now actually add the cells to the InDesign table
        for counter in range(max_cells * table_rows_number):
            temp_cell = etree.SubElement(inDesign_tabel, 'Cell')
            temp_cell.set('{http://ns.adobe.com/AdobeInDesign/4.0/}ccols', '1')
            # need to adjust the coll width depending on the numebr of columns
            temp_cell.set('{http://ns.adobe.com/AdobeInDesign/4.0/}ccolwidth', str(max_table_width / max_cells))
            temp_cell.set('{http://ns.adobe.com/AdobeInDesign/4.0/}crows', '1')
            temp_cell.set('{http://ns.adobe.com/AdobeInDesign/4.0/}table', 'cell')


        # now run through the InDesign table and add text
        InDesign_cell_counter = 0
        for row_counter in range(len(table_rows)):
            table_cells = table_rows[row_counter].xpath('td')
            for cell_counter in range(max_cells):
                if cell_counter < len(table_rows[row_counter]):
                    if row_counter == 0:
                        bold_para_heading = etree.Element('DebateTimingRubric')
                        bold_para_heading.text = table_cells[cell_counter].text
                        # remove extra new line from the end
                        if bold_para_heading.text is not None and bold_para_heading.text[-1] == '\n':
                            bold_para_heading.text = bold_para_heading.text[:-1]
                        inDesign_tabel[InDesign_cell_counter].append(bold_para_heading)
                        # inDesign_tabel[InDesign_cell_counter].set('{http://ns.adobe.com/AdobeInDesign/4.0/}theader', '')
                    else:
                        inDesign_tabel[InDesign_cell_counter].text = table_cells[cell_counter].text
                        # remove extra new line from the end
                        if inDesign_tabel[InDesign_cell_counter].text is not None and inDesign_tabel[InDesign_cell_counter].text[-1] == '\n':
                            inDesign_tabel[InDesign_cell_counter].text = inDesign_tabel[InDesign_cell_counter].text[:-1]
                InDesign_cell_counter += 1

        # if there is any tail text on the html, add it to the tail text of the InDesign table
        if table.tail is not None:
            inDesign_tabel.tail = table.tail

        # raplece the html table with an InDesign table
        table.getparent().replace(table, inDesign_tabel)
    if len(cdata_element) > 0 and cdata_element[-1].tail is None:
        cdata_element[-1].tail = '\n'
    elif len(cdata_element) > 0 and cdata_element[-1].tail is not None:
        cdata_element[-1].tail += '\n'
    elif cdata_element.text is not None:
        cdata_element.text += '\n'
    # return etree.tostring(cdata_element)
    return cdata_element


# return times in OP format
def format_time(time_string):
    if isinstance(time_string, str) and len(time_string.split(':')) >= 2:
        split_time = time_string.split(':')
        try:
            output_time = time(hour=int(split_time[0]), minute=int(split_time[1]))
        except:
            return None
        output_time = output_time.strftime('%I.%M%p')
        output_time = output_time.replace('AM', 'am').replace('PM', 'pm').replace('12.00pm', '12 noon')
        if output_time[0] == '0': output_time = output_time[1:]
        return output_time
    else:
        return None


# format date
def format_date(datetime_string):
    if isinstance(datetime_string, str) and len(datetime_string.split('-')) == 3:
        remove_time = datetime_string.split('T')[0]
        try:
            date_list = remove_time.split('-')
            # output_date = date.fromtimestamp(datetime_string)
            # print(output_date)
            output_date = date(int(date_list[0]), int(date_list[1]), int(date_list[2]))
            output_date = output_date.strftime('%A %d %B')
            output_date = output_date.replace(' 0', ' ')
        except:
            return None
        return output_date
    else:
        return None


def next_letter(old_letter):
    letters = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')
    if old_letter == '':
        return letters[0]
    else:
        if letters.index(old_letter[-1]) == 25:
            return old_letter + letters[0]
        else:
            return letters[letters.index(old_letter[-1]) + 1]


def dropns(root):
    """Remove all namespaces as we will not need them and they can get in the way."""
    for elem in root.iter():
        parts = elem.tag.split(':')
        if len(parts) > 1:
            elem.tag = parts[-1]
        entries = []
        for attrib in elem.attrib:
            if attrib.find(':') > -1:
                entries.append(attrib)
        for entry in entries:
            del elem.attrib[entry]
