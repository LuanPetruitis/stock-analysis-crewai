import json
import os
from datetime import datetime

import yfinance as yf

from crewai import Agent, Task, Crew, Process

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

# Fornece um método para construir uma aplicação web python de maneira rápida
import streamlit as st
# from IPython.display import Markdown


# ## Transformar esse método em uma ferramenta de IA é possível fazer com qualquer função



ticket = "AAPL"
def fetch_stock_price(ticket):
    return yf.download(ticket, start="2023-08-08", end="2024-08-08")

yahoo_finance_tool =  Tool(
    name="Yahoo Finance Tool",
    description="Fetches stock prices for {ticket}",
    func=lambda ticket: fetch_stock_price(ticket)
)


response = yahoo_finance_tool.run("AAPL")


# Caso vai fazer o Deploy -> https://share.streamlit.io/
# os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = "API_KEY"
llm = ChatOpenAI(
    model="gpt-3.5-turbo"
)


# # Criando o 1º Agent

# Parametros que podem ser usados DOCS => https://docs.crewai.com/core-concepts/Agents/#what-is-an-agent
stockPriceAnalyst = Agent(
    role="Senior stock price Analyst",
    goal="Find the {ticket} stock price and analyses trends",
    backstory="""You're a highly experienced in analyzing the price of an specific stock
    and make predictions about its future price.""",
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    allow_delegation=False,
    tools=[yahoo_finance_tool]
)



# Parametros que podem ser usados DOCS => https://docs.crewai.com/core-concepts/Tasks/
getStockPrice = Task(
    description="Analyze the stock {ticket} price history and create a trend analyses od up, down or sideways",
    expected_output="""Specify the current trend stock price - up, down or sideways,
    eg. stock='AAPL, price up'""",
    agent=stockPriceAnalyst
)



# Importando a tool de search
search_tool = DuckDuckGoSearchResults(backend='news', num_results=10)



newAnalyst = Agent(
    role="Stock News Analyst",
    goal="""Create a short summary of the market news related to the stock {ticket} company. Specify the current trend - up, down or sideways with the news context. For each request stock asset, specify a numbet between 0 and 100, where 0 is extreme fear and 100 is extreme greed.""",
    backstory="""You're highly experienced in analyzing the market trends and news and have tracked the assets for moree then 10 years.
    You're also master level analyts in the tradicional markets and have deep understanding of human psychology.
    You understand news, theirs titles and information, but you look at those with a health dose of skepticism.
    You consider also the source of the news articles.""",
    verbose=True,
    llm=llm,
    max_iter=10,
    memory=True,
    allow_delegation=False,
    tools=[search_tool]
)




getNews = Task(
    description=f"""Take the stock and always include BTC to it (if not request).
    Use the search tool to search each one individually.
    The current date is {datetime.now()}.
    Compose the results into a helpful report.""",
    expected_output="""A summary of the overall market and one sentence summary for each request asset.
    Include a fear/greed score for each asset based on the news. Use the format:
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE>""",
    agent=newAnalyst
)



stockAnalystWrite = Agent(
    role="Senior Stock Analyst Writer",
    goal="Analyze the trends price and news and write an insighfull compelling and informative 3 paragraph long newsletter based on the stock report and price trend.",
    backstory="""You're widely accepted as the best stock analyst in the market. You understand complex concepts and create compelling stories and narratives that resonate with wider audiences.
    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental analyses.
    You're able to hold multiple opinions when analyzing anything.""",
    verbose=True,
    llm=llm,
    max_iter=10,
    memory=True,
    allow_delegation=True # para poder delegar uma parte da tarefa dele para outros
)




writeAnalyses = Task(
    description="""Use the stock price trend and the stock news report to create an analyses and write the newsletter about the {ticket} company that is brief and highlights the most important points.
    Focus on the stock price trend, news and fear/greed score. What are the near future considerations?
    Include the previous analyses of stock trend and news summary.
    """,
    expected_output="""An eloquent 3 paragraphs newsletter formated as markdown in an easy readable manner. It should contain:

    - 3 bullets executive summary
    - Introduction - set the overall picture and spike up the interest
    - main part provides the meat of the analysis including the news summary and fead/greed scores
    - summary - key facts and concrete future trend prediction - up, down or sideways.
    """,
    agent=stockAnalystWrite,
    context=[getStockPrice, getNews]
)


# # Criar o nosso grupo de IA 
# 
# process
#     - Sequential as tasks vão rodar uma depois da outra
#     - Hierarchical organiza de maneira hierarquica conforme vai sendo demandado


crew = Crew(
    agents=[stockPriceAnalyst, newAnalyst, stockAnalystWrite],
    tasks=[getStockPrice, getNews, writeAnalyses],
    verbose=True,
    process=Process.hierarchical,
    full_output=True,
    share_crew=False,
    manager_llm=llm,
    max_iter=15
)




#results = crew.kickoff(inputs={'ticket': 'AAPL'})


# results.raw



# Markdown(results.raw)

# Construindo uma aplicação WEB
with st.sidebar:
    st.header('Enter the Stock to Research')

    with st.form(key='research_form'):
        topic = st.text_input("Select the ticket")
        submit_button = st.form_submit_button(label="Run Research")

if submit_button:
    if not topic:
        st.error("Please fill the ticket field")
    else:
        results = crew.kickoff(inputs={'ticket': topic})

        st.subheader("Results of your research:")
        st.write(results.raw)
