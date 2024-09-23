from __future__ import annotations

import math, random
from typing import Any, Type, TypeVar, Callable, Optional
from functools import wraps

import pygame as pg
from pygame.key import get_pressed
from pygame.rect import Rect
from pygame.font import Font, SysFont
from pygame.surface import Surface

from kit import Scene, Manager, GameConfig, GameManager, TicksManager, ContentManager

EntityViewT = TypeVar("EntityViewT", bound="EntityView")
EntityControllerT = TypeVar("EntityControllerT", bound="EntityController")

pg.init()


class TexturesManager(Manager, init=False):
    textures: dict[str, Surface]

    def __init__(self) -> None:
        super().__init__()

        content = ContentManager.get_instance()

        self.textures = {
            "grass-tile": content.load_image("assets/grass-tile.png"),

            "tree-0": content.load_image("assets/tree-0.png"),
            "tree-1": content.load_image("assets/tree-1.png"),
            "player-0-0": content.load_image("assets/player-0-0.png"),
            "player-0-1": content.load_image("assets/player-0-1.png"),
            "player-1": content.load_image("assets/player-1.png"),
            "unknown-entity": content.load_image("assets/unknown-entity.png"),
        }

    def get_texture(self, texture_name: str) -> Surface:
        return self.textures[texture_name]


# class EntityView:
#     rect: Rect
#     image: Surface

#     def __init__(self) -> None:
#         pass


# class EntityController:
#     tiles: list[Tile]
#     position: tuple[int, int]

#     is_alive: bool

#     def __init__(self, view_factory: type[EntityView], model_factory: type[EntityModel]) -> None:
#         self.view = EntityView()

#         self.rect = Rect()
#         self.tiles = []
#         self.position = position

#         self.is_alive = True

#         self.set_texture(texture_name)
#         self.move_to(position)

#     @update_tiles
#     def set_texture(self, texture_name: str) -> None:
#         textures = TexturesManager.get_instance()
        
#         self.image = textures.get_texture(texture_name)
#         self.rect = Rect(self.rect.topleft, self.image.size)

#     @update_tiles
#     def move_to(self, position: tuple[int, int]) -> None:
#         self.rect.x = position[0] - self.rect.w / 2
#         self.rect.y = position[1] - self.rect.h
#         self.position = position

#     def move_by(self, amount: tuple[int, int]) -> None:
#         x, y = self.position

#         self.move_to((x + amount[0], y + amount[1]))

#     def update(self) -> bool:
#         return self.is_alive


# class AnimatedEntity(Entity):
#     texture_index: int
#     texture_names: list[str]

#     def __init__(self, position: tuple[int, int], texture_names: list[str] = None) -> None:
#         super().__init__(position, texture_names[0])

#         self.texture_index = 0
#         self.texture_names = texture_names

#     def update(self) -> bool:
#         texture_name = self.texture_names[self.texture_index]

#         self.set_texture(texture_name)
#         self.texture_index = (self.texture_index + 1) % len(self.texture_names)

#         return self.is_alive


# def update_render_tiles(function: Callable) -> Callable:
#     @wraps(function)
#     def _(self: EntityModel, *args: Any, **kwds: Any) -> None:
#         tiles = TilesManager.get_instance()
#         entities = EntitiesManager.get_instance()

#         entity_view = entities.get_entity_view(self.entity_id)
        
#         for tile in self.render_tiles:
#             tile.remove_entity(entity_view)

#         function(self, *args, **kwds)

#         self.tiles = tiles.get_render_tiles(self.rect)

#         for tile in self.render_tiles:
#             tile.add_entity(entity_view)

#     return _





class TilesManager(Manager, init=False):
    chunks: dict[tuple[int, int], TilesChunk]
    
    def __init__(self) -> None:
        super().__init__()

        self.chunks = {}

    def create_chunk(self, position: tuple[int, int]) -> TilesChunk:
        chunk = TilesChunk(position)
        
        self.chunks[position] = chunk
        
        return chunk

    def get_tile(self, position: tuple[int, int]) -> Optional[Tile]:
        x, y = position

        cx, incx = divmod(x, 8)
        cy, incy = divmod(y, 8)

        chunk = self.chunks.get((cx, cy))

        if chunk is None:
            return None

        return chunk.get_tile((incx, incy))

    def add_entity(self, entity: EntityView) -> None:
        x, y = entity.get_render_position()

        chunk = self.chunks.get((x // 128, y // 128))
        chunk.add_entity(entity)

    def get_render_tiles(self, rect: Rect) -> list[Tile]:
        min_x, min_y = rect.topleft
        min_x, min_y = min_x // 16, min_y // 16
        max_x, max_y = rect.bottomright
        max_x, max_y = math.ceil(max_x / 16), math.ceil(max_y / 16)

        return list(filter(bool, (
            self.get_tile((x, y))
            for x in range(min_x, max_x)
            for y in range(min_y, max_y)
        )))
    
    def draw(self, screen: Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset

        self.chunks = {
            position: chunk
            for position, chunk in self.chunks.items()
            if chunk.update()
        }

        screen.fblits(
            (
                chunk.image, (ox + cx * 128, oy + cy * 128)
            )
            for (cx, cy), chunk in self.chunks.items()
        )


class TilesChunk:
    image: Surface
    tiles: list[Tile]
    position: tuple[int, int]

    is_alive: bool
    is_render_required: bool
    
    def __init__(self, position: tuple[int, int]) -> None:
        self.image = Surface((128, 128), pg.SRCALPHA)
        self.tiles = [
            Tile(self, (x, y), "grass-tile")
            for y in range(8)
            for x in range(8)
        ]
        self.position = position
        
        self.is_alive = True
        self.is_render_required = True

    def get_tile(self, position: tuple[int, int]) -> Tile:
        x, y = position

        return self.tiles[x + y * 8]

    def add_entity(self, entity: EntityView) -> None:
        ex, ey = entity.get_render_position()

        self.tiles[ex % 16 + ey % 16 * 16].add_entity(entity)

    def render(self) -> None:
        self.tiles = list(filter(Tile.update, self.tiles))
        self.image.fblits(
            (
                tile.image, (i % 8 * 16, i // 8 * 16)
            )
            for i, tile in enumerate(self.tiles)
            if tile.get_is_changed()
        )

    def update(self) -> bool:
        if self.is_render_required:
            self.render()

            self.is_render_required = False

        return self.is_alive


class Tile:
    image: Surface
    chunk: TilesChunk
    position: tuple[int, int]
    entities: dict[tuple[int, int], list[EntityView]]
    background_texture_name: str

    is_alive: bool
    is_changed: bool
    is_render_required: bool

    def __init__(
        self, 
        chunk: TilesChunk, 
        position: tuple[int, int], 
        background_texture_name: str
    ) -> None:
        self.image = Surface((1, 1))
        self.chunk = chunk
        self.position = position
        self.entities = {}
        self.background_texture_name = background_texture_name

        self.is_alive = True
        self.is_changed = True
        self.is_render_required = True

    def add_entity(self, entity: EntityView) -> None:
        position = self.get_inner_position(entity.get_render_position())
        entities = self.entities.get(position)

        if entities is None:
            self.entities[position] = [entity]
        else:
            entities.append(entity)

        self.is_changed = True
        self.is_render_required = True
        self.chunk.is_render_required = True

    def remove_entity(self, entity: EntityView) -> None:
        position = self.get_inner_position(entity.get_render_position())
        entities = self.entities[position]

        if len(entities) == 1:
            del self.entities[position]
        else:
            entities.remove(entity)
        
        self.is_changed = True
        self.is_render_required = True
        self.chunk.is_render_required = True

    def get_inner_position(self, position: tuple[int, int]) -> tuple[int, int]:
        x, y = position
        tx, ty = self.position
        cx, cy = self.chunk.position

        return x - tx * 16 - cx * 128, y - ty * 16 - cy * 128

    def get_is_changed(self) -> bool:
        if self.is_changed:
            self.is_changed = False
            
            return True
        
        return False

    def render(self) -> None:
        textures = TexturesManager.get_instance()

        self.image = textures.get_texture(self.background_texture_name).copy()
        self.image.fblits(
            (entity.get_image(), position)
            for entity, position in sorted((
                (entity, position)
                for position, entities in self.entities.items()
                for entity in entities
            ), key=lambda t: t[0].get_y())
        )

    def update(self) -> bool:
        if self.is_render_required:
            self.render()

            self.is_render_required = False

        return self.is_alive


class MainScene(Scene):
    game: GameManager
    font: Font
    ticks: TicksManager

    tiles: TilesManager
    fps_text: Surface

    def initialize(self) -> None:
        self.game = Game.get_instance()
        self.font = SysFont("Arial", 12)
        self.ticks = self.game.ticks
        self.ticks.register(1, self.update)
        self.ticks.register(5, self.render_fps)

        TexturesManager()

        self.tiles = TilesManager()
        self.entities = EntitiesManager()

        for x in range(4):
            for y in range(2):
                self.tiles.create_chunk((x, y))

        self.player = self.entities.create_entity(
            EntityModel((0, 0), "player-0-1")
        )[1]

        self.render_fps()

    def update(self) -> None:
        self.entities.update()

        speed = 1
        state = get_pressed()

        x, y = 0, 0

        if state[pg.K_a]:
            x -= speed
        if state[pg.K_d]:
            x += speed
        if state[pg.K_w]:
            y -= speed
        if state[pg.K_s]:
            y += speed

        if x or y:
            self.player.move_by((x, y))

    def render_fps(self) -> None:
        fps = self.game.fps

        if math.isfinite(fps):
            fps = int(fps)

        self.fps_text = self.font.render(f"{fps} fps", False, (255, 0, 0))

    def draw(self) -> None:
        super().draw()

        screen_width = self.game.screen.get_width()

        self.tiles.draw(self.game.screen, (0, 16))
        self.game.screen.blit(self.fps_text, (screen_width - self.fps_text.get_width(), 0))


class Game(GameManager, init=False):
    def initialize(self) -> None:
        self.scene_manager.add_scene("main-scene", MainScene())
        self.scene_manager.set_current("main-scene")

        super().initialize()


if __name__ == "__main__":
    game = Game(
        config=GameConfig(
            flags=pg.SCALED | pg.DOUBLEBUF | pg.FULLSCREEN,
            screen_size=(512, 288)
        )
    )

    game.run()
