from __future__ import annotations

import time
from typing import Type, TypeVar, Callable, Optional
from dataclasses import dataclass

import pygame as pg
from pygame.time import Clock
from pygame.event import get as get_events
from pygame.image import load as pg_load
from pygame.surface import Surface
from pygame.display import flip, set_mode

T = TypeVar("T")



def nround(number: float) -> int:
    inumber = int(number)
    real = number - inumber
    sign = real >= 0
    
    if sign:
        return inumber if real < 0.5 else inumber + 1
    
    return inumber if real > -0.5 else inumber - 1


@dataclass
class GameConfig:
    flags: int
    screen_size: tuple[int, int]

    @classmethod
    def default(cls) -> GameConfig:
        return GameConfig(
            flags=0,
            screen_size=(800, 600)
        )


class Manager:
    _instance: Manager

    def __init_subclass__(cls, init: bool = True) -> None:
        if init:
            cls()

    def __init__(self) -> None:
        for cls in self.__class__.__mro__:
            if cls is not Manager and Manager in cls.__mro__:
                cls.set_instance(self)

    @classmethod
    def set_instance(cls, instance: Manager) -> None:
        cls._instance = instance

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        return cls._instance


class TicksManager(Manager):
    ticks: int
    listeners: list[tuple[int, Callable, int]]

    def __init__(self) -> None:
        super().__init__()

        self.ticks = 0
        self.listeners = []

    def update(self) -> None:
        self.ticks += 1

        for ticks, listener, offset in self.listeners:
            if (self.ticks + offset) % ticks == 0:
                listener()

    def register(self, ticks: int, listener: Callable, offset: int = 0) -> None:
        self.listeners.append((ticks, listener, offset))


class ContentManager(Manager):
    def load_image(self, path: str) -> Surface:
        return pg_load(path).convert_alpha()


class Scene:
    game: GameManager

    def __init__(self) -> None:
        self.game = GameManager.get_instance()

    def initialize(self) -> None:
        ...

    def draw(self) -> None:
        self.game.screen.fill((0, 0, 0))


class SceneManager(Manager):
    scenes: dict[str, Scene]
    current_scene: Optional[Scene]

    def __init__(self) -> None:
        super().__init__()
        
        self.scenes = {}
        self.current_scene = None

    def add_scene(self, name: str, scene: Scene) -> None:
        self.scenes[name] = scene
    
    def set_current(self, name: str) -> None:
        self.current_scene = self.scenes[name]

    def check_current_scene(self) -> None:
        if self.current_scene is None:
            raise ValueError("Current scene didn't set yet")
 
    def initialize(self) -> None:
        self.check_current_scene()
        self.current_scene.initialize()

    def draw(self) -> None:
        self.check_current_scene()
        self.current_scene.draw()


class GameManager(Manager, init=False):
    fps: float
    clock: Clock
    ticks: TicksManager
    screen: Surface
    scene_manager: SceneManager

    _draw_interval: float
    _update_interval: float

    def __init__(self, config: GameConfig = GameConfig.default()) -> None:
        super().__init__()

        self.fps = 0
        self.clock = Clock()
        self.ticks = TicksManager.get_instance()
        self.screen = set_mode(
            size=config.screen_size, 
            flags=config.flags
        )
        self.scene_manager = SceneManager.get_instance()

        self._draw_interval = 1 / 2400
        self._update_interval = 1 / 60

    def initialize(self) -> None:
        self.scene_manager.initialize()

    def update(self) -> None:
        self.ticks.update()

    def draw(self) -> None:
        self.scene_manager.draw()

        flip()

    def run(self) -> None:
        last_draw_time = 0
        last_update_time = 0

        self.initialize()

        while 1:
            current_time = time.time()

            if current_time - last_update_time > self._update_interval:
                self.update()

                last_update_time = current_time

            if current_time - last_draw_time > self._draw_interval:
                for event in get_events():
                    if event.type == pg.QUIT:
                        exit()

                self.draw()

                last_draw_time = current_time

            self.fps = self.clock.get_fps()
            self.clock.tick(2400)
