# Smart Houses

#### This repository was created by Deborah Dore and Vincenzo Imperati.

Lately, improving electricity use in homes is becoming more and more critical. Enhancing electricity usage is possible through the Demand Response algorithm that allows users to manage their energy consumption correctly, reply better to peak demand or electricity market offers and utilise the energy resources more efficiently.
This work proposes an hour-ahead Demand Response algorithm for Home Energy Man- agement System (HEMS) that uses machine learning techniques, considering electricity costs and client’s dissatisfaction.
Specifically, because of the inherent nature in hour-ahead electricity price market, the customer accesses only one price for the current hour. To deal with the uncertainty in future prices, a stable price forecasting model is presented, which is implemented by a Long Short-Term Memory (LSTM). A particular Recurrent Neural Network capable of learning long-term dependencies.
Price’s prediction has become an essential argument in today’s electrical engineering, and numerous methods have been tested for its implementation. The LSTM method is easy and efficient to implement, showing good predictions due to the nature of the prices: a time series strictly correlated.
Figure 1 shows the detailed DR algorithm that combines the long short-term memory and multi-agent reinforcement learning. Every hour, the HEMS receives the hour-ahead price, and uses the LSTM to predict the future prices (twelve hours forecasted). In cooperation with the forecasted future prices, MARL is adopted to make optimal decisions for differ- ent appliances in a decentralized manner, to minimize the user energy bill and degree of discomfort. Here, each appliance has an agent, and RL is used for decision-making in the context of uncertainty regarding the price information and load demand of the appliances.


- The main file used to start the fist phase of the project is [this](main.py): you can start the file in *test mode* by
  adding *True* when executing the file.

- The main file used to start the **second** phase of the project is [this](RL/main.py). In order to start the
  reinforcement learning, you must choose a list of houses that you want simulate from *muratori_5* directory. for each
  house chosen you must insert in the corresponding house folder the files of devices that you want insert in simulation
  of the corresponding house.
  
  
#### [Here](Smart%20Houses.pdf) you can find an exhaustive description of the project.

