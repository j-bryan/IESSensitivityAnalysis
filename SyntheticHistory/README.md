We're refitting the ARMA models to price only using the SyntheticHistory ROM.
The primary motivator for this work is to reduce the computational expense of solving the dispatch of a HERON model over the synthetic history.
Computationally efficient time series models will minimize **number of clusters** and **segment length** while still effectively capturing the marginal distribution and autocorrelative behavior of the historical data.
Price-taker assumptions allow us to focus on only price.
This allows us to use the SyntheticHistory ROM, since we avoid the problematic SOLAR data, for which the SyntheticHistory ROM currently lacks adequate features.
