import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
    CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY
import random


class SentdeBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.distribute_workers()  # in sc2/bot_ai.py
        await self.build_workers()  # workers bc obviously
        await self.build_pylons()  # pylons are protoss supply buildings
        await self.expand()  # expand to a new resource area.
        await self.build_assimilator()  # getting gas
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        await self.attack()


    async def build_workers(self):
        # nexus = command center
        for nexus in self.units(NEXUS).ready.noqueue:
            # we want at least 20 workers, otherwise let's allocate 70% of our supply to workers.
            # later we should use some sort of regression algo maybe for this?
            if self.units(PROBE).amount < 60:
                if self.can_afford(PROBE):
                    await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        margen_supply = self.supply_cap / 15 + 4
        if self.supply_left < margen_supply:
            build_pylon = True
            if self.supply_cap < 50:
                if self.already_pending(PYLON):
                    build_pylon = False

            if build_pylon:
                if self.can_afford(PYLON):
                    nexus = random.choice(self.units(NEXUS))
                    await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 7))

    async def expand(self):
        construir_nexus = False
        if self.units(NEXUS).amount == 1:
            construir_nexus = True
        else:
            relacion_nexus = self.supply_cap / self.units(NEXUS).amount
            if relacion_nexus >= 30:
                construir_nexus = True
        if construir_nexus:
            if self.can_afford(NEXUS) and not self.already_pending(NEXUS):
                await self.expand_now()

    async def build_assimilator(self):
        if self.units(PYLON).exists:
            for nexus in self.units(NEXUS).ready:
                vaspenes = self.state.vespene_geyser.closer_than(10.0, nexus)
                for vaspene in vaspenes:
                    if not self.can_afford(ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                        await self.do(worker.build(ASSIMILATOR, vaspene))
                        # recolectar minerales despues (encolar accion True)
                        mf = self.state.mineral_field.closest_to(worker)
                        await self.do(worker.gather(mf, queue=True))

    async def offensive_force_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).ready.exists:
                if not self.units(CYBERNETICSCORE):
                    if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                        await self.build(CYBERNETICSCORE, near=pylon)
                else:
                    relacion_gateway = self.supply_cap / self.units(GATEWAY).amount
                    if relacion_gateway >= 40:
                        if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                            await self.build(GATEWAY, near=pylon)
            else:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)

            if self.units(CYBERNETICSCORE).ready.exists and self.units(NEXUS).amount > 1:
                construir_stargate = False
                if self.units(STARGATE).amount == 0:
                    construir_stargate = True
                else:
                    relacion_stargate = self.supply_cap / self.units(STARGATE).amount
                    if relacion_stargate >= 65:
                        construir_stargate = True
                if construir_stargate:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        await self.build(STARGATE, near=pylon)

    
    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0:
                await self.do(gw.train(STALKER))

        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        # {UNIT: [n to fight, n to defend]}
        aggressive_units = {STALKER: [14, 4],
                            VOIDRAY: [5, 1]}

        ataque_total = True
        for UNIT in aggressive_units:
            if self.units(UNIT).amount < aggressive_units[UNIT][0]:
                ataque_total = False
        if ataque_total:
            for UNIT in aggressive_units:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

        else:
            defensa = True
            for UNIT in aggressive_units:
                if self.units(UNIT).amount < aggressive_units[UNIT][1]:
                    defensa = False
            if defensa:
                if len(self.known_enemy_units) > 0 and len(self.known_enemy_units) < self.units.amount:
                    for UNIT in aggressive_units:
                        for s in self.units(UNIT).idle:
                            await self.do(s.attack(random.choice(self.known_enemy_units)))



run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Protoss, SentdeBot()),
    Computer(Race.Protoss, Difficulty.VeryHard)
], realtime=False)
