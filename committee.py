from framework.framework import Delegate 

usa = Delegate("USA", "Mike Waltz", "USA", "Currently at war with Iran")
iran = Delegate("IRN", "Nasrollah Entezam", "Iran", "Currently at war with the USA and Israel")
israel = Delegate("ISR", "Nasrollah Entezam", "Israel", "Currently at war with Iran, allies with USA")
france = Delegate("FRA", "Jérôme Bonnafont", "France", "Neutral in conflict but can intervene")

committee = [usa, iran, israel, france]