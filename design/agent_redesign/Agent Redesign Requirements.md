# Agent Redesign Requirements


## Arbitrary bid curves
The economists really want more flexibility in how the devices bid and to support this we need to be able to create arbitrary bid curves. DSOT used a four-point bid curve with linear response to price with a deadband around a nominal price. I (Trevor) don't know how this was translated into bids and how this was aggregated up by DSO. I know the bid that was sent to the wholesale market consisted of a fixed block bid and a quadratic price-responsive bid.
