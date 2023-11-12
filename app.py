from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import numpy as np
import uuid
import streamlit as st
import base64

bge_tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-large-en-v1.5')
bge_model = AutoModel.from_pretrained('BAAI/bge-large-en-v1.5')

def web_scraping_seli(url):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    # Enable JavaScript and cookies
    chrome_options.add_argument('--enable-javascript')
    chrome_options.add_argument('--enable-cookies')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    # Initialize the WebDriver with Chrome options
    driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(30) 
    driver.get(url)
    time.sleep(15) 
    page_source = driver.page_source
    # Quit the browser
    driver.quit()
    soup = BeautifulSoup(page_source, 'html.parser')
    return soup

def web_scraping(search_term):

    url = 'https://ascopubs.org/action/doSearch?AllField='+search_term+'&ConceptID=' 

    date_url = 'https://ascopubs.org/action/doSearch?AllField='+search_term+'&ConceptID=&startPage=&sortBy=Ppub'

    soup = web_scraping_seli(url)

    date_soup = web_scraping_seli(date_url)

    art_title_soup = soup.find_all('div', class_='art_title')

    art_title_date_soup = date_soup.find_all('div', class_='art_title')

    art_title_year = soup.find_all('div', class_='publication-meta')

    art_title_date_year= date_soup.find_all('div', class_='publication-meta')

    if len(art_title_soup) == 0:
        st.write('THERE IS NO DATA TO SCRAPE FOR TERM YOU HAVE PROVIDED.')
        return pd.DataFrame()

    all_titles=[]
    all_href_link=[]
    complete_text=[]
    all_abstract = []
    abstract_flag = []
    text_id = []
    publication_year = []

    figure_table_list = []
    figureCaption_list = []
    text_image_id = []

    main_url = 'https://ascopubs.org'
    
    st.markdown(f'<span style="color:blue">WEB SCRAPER SEARCH TERM : </span>{search_term}',  unsafe_allow_html=True)

    count =0 
    #TITLES, SUB_LINKS
    for i in range(len(art_title_soup)):
        title = art_title_soup[i]
        anchor_element = title.find_all('a')
        href_link = anchor_element[0].get('href')
        st.markdown(f'<span style="color:red">LINK : </span> {main_url + href_link}', unsafe_allow_html=True)
        if main_url + href_link in all_href_link:
            continue
        else:
            all_href_link.append(main_url + href_link)

        title_text = str(title.get_text())
        all_titles.append(title_text)
        st.markdown(f'<span style="color:red">TITLE : </span> {title_text}',  unsafe_allow_html=True)

        year = art_title_year[i].find('span', class_ = 'publication-year')
        if year is not None:
            publication_year.append(year.get_text())
        else:
            publication_year.append(year)

        st.markdown(f'<span style="color:red">YEAR : </span> {year}', unsafe_allow_html=True)
        st.markdown(f'<hr>', unsafe_allow_html=True)

        count+=1
        if count==10:
            count=0
            break;
    
    for j in range(len(art_title_date_soup)):
        title = art_title_date_soup[j]

        anchor_element = title.find_all('a')
        href_link = anchor_element[0].get('href')
        st.markdown(f'<span style="color:red">LINK : </span> {main_url + href_link}', unsafe_allow_html=True)
        if main_url + href_link in all_href_link:
            continue
        else:
            all_href_link.append(main_url + href_link)

        title_text = str(title.get_text())
        all_titles.append(title_text)
        st.markdown(f'<span style="color:red">TITLE : </span> {title_text}',  unsafe_allow_html=True)

        year = art_title_date_year[j].find('span', class_ = 'publication-year')
        if year is not None:
            publication_year.append(year.get_text())
        else:
            publication_year.append(year)

        st.markdown(f'<span style="color:red">YEAR : </span> {year}', unsafe_allow_html=True)
        st.markdown(f'<hr>', unsafe_allow_html=True)
        
        count+=1
        if count==10:
            count=0
            break;

    progress_bar = st.progress(0)

    #FULL TEXT, ABSTRACT , FIGURES AND TABLES
    for i in range(len(all_href_link)):
        
        progress = (i + 1) / len(all_href_link)
        progress_bar.progress(progress)

        url = all_href_link[i]

        print(url)

        start = time.time()
        # url='https://ascopubs.org/doi/full/10.1200/JCO.2007.15.4393'
        sublink_soup = web_scraping_seli(url)
        ul_nav = sublink_soup.find_all('ul', class_='tab-nav')
        li_elements = ul_nav[0].find_all('li')

        text_elements = []
        elements=[]
        fulltext = ' '
        introduction_text = ' '

        unique_id = str(uuid.uuid4())
        text_id.append(unique_id)

        for list_ele in li_elements:
            text_elements.append(list_ele.get_text(strip=True))
            elements.append(list_ele)

        if 'Figures and Tables' in text_elements:
            index = text_elements.index('Figures and Tables')
            anchor_element = elements[index].find_all('a')
            href_link = anchor_element[0].get('href')
            tablink_soup = web_scraping_seli(main_url+href_link)
            publication_page = tablink_soup.find('div', class_='publication-tabs')
            figure_table_widget = publication_page.find('div', class_='tabs-widget')
            if figure_table_widget is not None:
                figure_table_content = figure_table_widget.find('div', class_='tab-content')
                if figure_table_content is not None:
                    figure_table_pane = figure_table_content.find_all('div', class_='tab-pane')
                    figure_table_article = figure_table_pane[0].find('article')
                    figure_table= figure_table_article.find_all('div', class_= 'figuresContent')
                    if figure_table is not None:
                        for figure_table_info in figure_table:
                            all_fig = figure_table_info.find_all('div', class_='figure-image-content')
                            for fig in all_fig:
                                figure_table_holder = fig.find('div',class_='holder')
                                figureCaption = figure_table_holder.find('div',class_='figureCaption')
                                figureCaption_list.append(figureCaption.get_text(strip=True))
                                image = figure_table_holder.find('a', class_='thumbnail showFiguresEEvent').find('img')
                                figure_table_list.append(main_url + image.get('src'))
                                text_image_id.append(unique_id)
                            all_table_dis = figure_table_info.find_all('center', class_='fulltext')
                            all_table_img = figure_table_info.find_all('div', class_='tableWrapper')
                            for i in range(len(all_table_dis)):
                                table_wrap = all_table_img[i].find('div', class_='NLM_table-wrap')
                                figureCaption_list.append(all_table_dis[i].get_text(strip=True))
                                table_html = table_wrap.find('table')
                                if table_html is None:
                                    figure_table_list.append(main_url + table_wrap.find('a').get('href'))
                                else:
                                    figure_table_list.append(table_html)
                                text_image_id.append(unique_id)
            print('Figures and Tables')

        if 'Full Text' in text_elements: 
            index = text_elements.index('Full Text')
            anchor_element = elements[index].find_all('a')
            href_link = anchor_element[0].get('href')
            tablink_soup = web_scraping_seli(main_url+href_link)
            fulltext_info = tablink_soup.find('div', class_='hlFld-Fulltext')
            if fulltext_info is not None: 
                fulltext_list = fulltext_info.find_all('div', class_='NLM_sec')
                if fulltext_list is not None:
                    for sub_text in fulltext_list:
                        intro_list = sub_text.find_all('p')
                        sectionHeading = sub_text.find_all('div', class_='sectionHeading')
                        sub_list = sub_text.find_all('div', class_='NLM_sec')
                        for sect_Head in sectionHeading:
                            fulltext = fulltext + ' ' + str(sect_Head.get_text(strip=True)) + '\n'
                        for intro_text in intro_list:
                            fulltext = fulltext + ' ' + str(intro_text.get_text(strip=True)) + '\n'
                        for sub_text in sub_list:
                            fulltext = fulltext + ' ' + str(sub_text.get_text(strip=True))  + '\n'
                    complete_text.append(fulltext)
                else:
                    print(url)
                    complete_text.append('NO TEXT CAN SCRAPED FOR THIS ARTICLE BCOZ OF ACCESS ISSUE')
            else:
                print('hi',url)
                complete_text.append('NO TEXT CAN SCRAPED FOR THIS ARTICLE BCOZ OF ACCESS ISSUE')

        if 'Abstract' in text_elements:  
            index = text_elements.index('Abstract')
            anchor_element = elements[index].find_all('a')
            href_link = anchor_element[0].get('href')
            abstract_info = tablink_soup.find('div', class_='abstractSection abstractInFull')
            abstract_text = abstract_info.get_text(separator=' ')
            all_abstract.append(abstract_text)
            abstract_flag.append(0)
        else:
            index = text_elements.index('Full Text')
            anchor_element = elements[index].find_all('a')
            href_link = anchor_element[0].get('href')
            tablink_soup = web_scraping_seli(main_url+href_link)
            abstract_info = tablink_soup.find('div', class_='hlFld-Fulltext') 
            if abstract_info is not None: 
                abstract_list = fulltext_info.find_all('div', class_='NLM_sec-type_introduction')
                if abstract_list is not None: 
                    for sub_text in abstract_list:
                        intro_list = sub_text.find_all('p')
                        for intro in intro_list:
                            introduction_text = introduction_text + ' ' + str(intro.get_text()) + '\n'
                    if introduction_text == ' ':
                        all_abstract.append('No ABSTRACT OR INTRODUCTION HAS FOUND')
                    else:
                        all_abstract.append(introduction_text)
                    abstract_flag.append(1)
                else:
                    all_abstract.append('No ABSTRACT OR INTRODUCTION HAS FOUND')
                    abstract_flag.append(2)
            else:
                all_abstract.append('No ABSTRACT OR INTRODUCTION HAS FOUND')
                abstract_flag.append(2)
        end = time.time()
        print(end-start)

    #TOKENIZATION
    abs_token_len =[]
    # abs_token_embed = []
    complete_text_len = []
    for i in range(len(all_abstract)):
        abs_token = bge_tokenizer(all_abstract[i], return_tensors="pt")
        abs_token_len.append(len(abs_token.input_ids[0]))
        # max_length = 512
        # abs_token_embed.append(bge_model(abs_token.input_ids[0][0:max_length].unsqueeze(0)))

        complete_text_token = bge_tokenizer(complete_text[i], return_tensors="pt")
        complete_text_len.append(len(complete_text_token.input_ids[0]))

    #CREATING DATAFRAME FOR THE RESULT
    data = {
        'Search_term' : search_term,
        'Titles': all_titles,
        'URL': all_href_link,
        'Abstract_flag':abstract_flag,
        'Abstract': all_abstract,
        'Complete Text': complete_text,
        'Abs_token_len' : abs_token_len,
        'Complete_text_len':complete_text_len,
        'text_image_id' : text_id,
        'publication_year': publication_year
    }

    df = pd.DataFrame(data)
    # np.save(search_term + '.npy', abs_token_embed)
    # Save the DataFrame as a CSV file
    df.to_csv('scraped_data/'+search_term + '.csv', index=False)

    #CREATING DATAFRAME FOR THE RESULT
    image_data = {
        'figure_table_list' : figure_table_list,
        'figureCaption_list' : figureCaption_list,
        'text_image_id' : text_image_id
    }

    image_df = pd.DataFrame(image_data)
    # np.save(search_term + '.npy', abs_token_embed)
    # Save the DataFrame as a CSV file
    image_df.to_csv('scraped_image_data/' + search_term + '_image.csv', index=False)

    return df

st.title("MEDICAL DATA - WEB SCRAPING TOOL")

main_url = 'https://ascopubs.org'

st.write('Website Name : ', main_url)

search_term = st.text_input("Enter search term that has to be scraped")
if st.button("Scrape"):
    if search_term:
        scraped_data = web_scraping(search_term)
        st.markdown(f'<span style="color:red">RESULT : </span>',  unsafe_allow_html=True)
        st.dataframe(scraped_data)
        # Add a download button
        def download_csv(data):
            csv_file = data.to_csv(index=False).encode('utf-8')
            b64 = base64.b64encode(csv_file).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="scraped_data.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
        download_csv(scraped_data)