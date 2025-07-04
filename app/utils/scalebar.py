# -*- coding: utf-8 -*-
"""
Utilitários para geração de scale bars e legendas para visualizações geoespaciais.

Classes e funções para criar barras de cores, legendas e outros elementos visuais
para mapas e visualizações de dados geoespaciais.
"""

import base64
import io
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional, Dict, Union

from PIL import Image, ImageDraw, ImageFont


class Orientation(str, Enum):
    """Orientações disponíveis para scale bars."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class LabelPosition(str, Enum):
    """Posições de labels em scale bars."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    INSIDE = "inside"


@dataclass
class ColorStop:
    """Representa um ponto de cor em um gradiente."""
    position: float  # 0.0 a 1.0
    color: Tuple[int, int, int]  # RGB
    label: Optional[str] = None


@dataclass
class ScaleBarConfig:
    """Configuração para geração de scale bar."""
    width: int = 300
    height: int = 50
    orientation: Orientation = Orientation.HORIZONTAL
    show_labels: bool = True
    font_size: int = 12
    font_family: str = "arial.ttf"
    background_color: Tuple[int, int, int, int] = (255, 255, 255, 0)  # RGBA
    border_color: Tuple[int, int, int] = (0, 0, 0)
    border_width: int = 1
    label_color: Tuple[int, int, int] = (0, 0, 0)
    label_position: LabelPosition = LabelPosition.BOTTOM
    margin: int = 15
    tick_length: int = 3
    continuous: bool = True  # Se True, gradiente contínuo; se False, cores discretas


class ScaleBarGenerator:
    """Gerador de scale bars para visualizações geoespaciais."""

    def __init__(self, config: Optional[ScaleBarConfig] = None):
        """
        Inicializa o gerador com configuração padrão ou personalizada.

        Args:
            config: Configuração do scale bar
        """
        self.config = config or ScaleBarConfig()
        self._font_cache = {}

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        Converte cor hexadecimal para RGB.

        Args:
            hex_color: Cor em formato hex (com ou sem #)

        Returns:
            Tupla RGB
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def interpolate_color(
            color1: Tuple[int, int, int],
            color2: Tuple[int, int, int],
            fraction: float
    ) -> Tuple[int, int, int]:
        """
        Interpola entre duas cores RGB.

        Args:
            color1: Primeira cor RGB
            color2: Segunda cor RGB
            fraction: Fração de interpolação (0.0 a 1.0)

        Returns:
            Cor interpolada
        """
        return tuple(
            int(color1[i] * (1 - fraction) + color2[i] * fraction)
            for i in range(3)
        )

    def _get_font(self, size: Optional[int] = None):
        """
        Obtém fonte com cache.

        Args:
            size: Tamanho da fonte (usa config se None)

        Returns:
            Objeto fonte
        """
        size = size or self.config.font_size

        if size not in self._font_cache:
            try:
                self._font_cache[size] = ImageFont.truetype(
                    self.config.font_family, size
                )
            except:
                self._font_cache[size] = ImageFont.load_default()

        return self._font_cache[size]

    def create_gradient(
            self,
            colors: List[Tuple[int, int, int]],
            width: int,
            height: int,
            orientation: Orientation = Orientation.HORIZONTAL,
            continuous: bool = True
    ) -> Image.Image:
        """
        Cria uma imagem de gradiente.

        Args:
            colors: Lista de cores RGB
            width: Largura da imagem
            height: Altura da imagem
            orientation: Orientação do gradiente
            continuous: Se True, gradiente suave; se False, blocos de cor

        Returns:
            Imagem PIL com gradiente
        """
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        if continuous:
            # Gradiente contínuo
            if orientation == Orientation.HORIZONTAL:
                for x in range(width):
                    position = x / (width - 1) if width > 1 else 0
                    color = self._get_color_at_position(colors, position)
                    draw.rectangle([x, 0, x, height - 1], fill=color)
            else:
                for y in range(height):
                    position = 1 - (y / (height - 1) if height > 1 else 0)
                    color = self._get_color_at_position(colors, position)
                    draw.rectangle([0, y, width - 1, y], fill=color)
        else:
            # Blocos discretos de cor
            num_colors = len(colors)
            if orientation == Orientation.HORIZONTAL:
                block_width = width / num_colors
                for i, color in enumerate(colors):
                    x_start = int(i * block_width)
                    x_end = int((i + 1) * block_width)
                    draw.rectangle([x_start, 0, x_end - 1, height - 1], fill=color)
            else:
                block_height = height / num_colors
                for i, color in enumerate(reversed(colors)):
                    y_start = int(i * block_height)
                    y_end = int((i + 1) * block_height)
                    draw.rectangle([0, y_start, width - 1, y_end - 1], fill=color)

        return img

    def _get_color_at_position(
            self,
            colors: List[Tuple[int, int, int]],
            position: float
    ) -> Tuple[int, int, int]:
        """
        Obtém cor interpolada em uma posição específica.

        Args:
            colors: Lista de cores
            position: Posição (0.0 a 1.0)

        Returns:
            Cor RGB interpolada
        """
        if len(colors) == 1:
            return colors[0]

        # Calcular índice e fração
        color_index = position * (len(colors) - 1)
        lower_idx = int(color_index)
        upper_idx = min(lower_idx + 1, len(colors) - 1)
        fraction = color_index - lower_idx

        return self.interpolate_color(
            colors[lower_idx],
            colors[upper_idx],
            fraction
        )

    def create_scale_bar(
            self,
            colors: List[Union[str, Tuple[int, int, int]]],
            min_value: float,
            max_value: float,
            unit: str = "",
            title: str = "",
            intermediate_values: Optional[List[float]] = None,
            custom_labels: Optional[Dict[float, str]] = None
    ) -> Image.Image:
        """
        Cria uma scale bar completa com labels e título.

        Args:
            colors: Lista de cores (hex ou RGB)
            min_value: Valor mínimo
            max_value: Valor máximo
            unit: Unidade de medida
            title: Título da scale bar
            intermediate_values: Valores intermediários para mostrar
            custom_labels: Labels customizados para valores específicos

        Returns:
            Imagem PIL da scale bar completa
        """
        # Converter cores hex para RGB se necessário
        rgb_colors = []
        for color in colors:
            if isinstance(color, str):
                rgb_colors.append(self.hex_to_rgb(color))
            else:
                rgb_colors.append(color)

        # Calcular dimensões totais
        margin = self.config.margin if self.config.show_labels else 10
        total_width = self.config.width + (2 * margin)
        total_height = self.config.height + (2 * margin)

        # Ajustar para orientação vertical
        if self.config.orientation == Orientation.VERTICAL:
            self.config.width, self.config.height = self.config.height, self.config.width
            total_width, total_height = total_height, total_width

        # Criar imagem principal
        img = Image.new('RGBA', (total_width, total_height), self.config.background_color)

        # Criar e colar gradiente
        gradient = self.create_gradient(
            rgb_colors,
            self.config.width,
            self.config.height,
            self.config.orientation,
            self.config.continuous
        )

        bar_x = margin
        bar_y = margin
        img.paste(gradient, (bar_x, bar_y))

        # Adicionar borda
        draw = ImageDraw.Draw(img)
        if self.config.border_width > 0:
            draw.rectangle(
                [bar_x, bar_y, bar_x + self.config.width - 1, bar_y + self.config.height - 1],
                outline=self.config.border_color,
                width=self.config.border_width
            )

        # Adicionar labels se habilitado
        if self.config.show_labels:
            self._add_labels(
                draw,
                bar_x,
                bar_y,
                min_value,
                max_value,
                unit,
                title,
                intermediate_values,
                custom_labels
            )

        return img

    def _add_labels(
            self,
            draw: ImageDraw.Draw,
            bar_x: int,
            bar_y: int,
            min_value: float,
            max_value: float,
            unit: str,
            title: str,
            intermediate_values: Optional[List[float]] = None,
            custom_labels: Optional[Dict[float, str]] = None
    ):
        """Adiciona labels à scale bar."""
        font = self._get_font()

        # Preparar labels
        custom_labels = custom_labels or {}
        min_label = custom_labels.get(min_value, f"{min_value}{unit}")
        max_label = custom_labels.get(max_value, f"{max_value}{unit}")

        if self.config.orientation == Orientation.HORIZONTAL:
            # Labels horizontais
            y_offset = -self.config.font_size - 5 if self.config.label_position == LabelPosition.TOP else self.config.height + 5

            # Min e max
            draw.text(
                (bar_x, bar_y + y_offset),
                min_label,
                fill=self.config.label_color,
                font=font,
                anchor="lm" if self.config.label_position == LabelPosition.BOTTOM else "lb"
            )
            draw.text(
                (bar_x + self.config.width, bar_y + y_offset),
                max_label,
                fill=self.config.label_color,
                font=font,
                anchor="rm" if self.config.label_position == LabelPosition.BOTTOM else "rb"
            )

            # Valores intermediários
            if intermediate_values:
                for value in intermediate_values:
                    if min_value < value < max_value:
                        x_pos = bar_x + int(((value - min_value) / (max_value - min_value)) * self.config.width)
                        label = custom_labels.get(value, f"{value}{unit}")
                        draw.text(
                            (x_pos, bar_y + y_offset),
                            label,
                            fill=self.config.label_color,
                            font=font,
                            anchor="mm" if self.config.label_position == LabelPosition.BOTTOM else "mb"
                        )
                        # Tick mark
                        if self.config.tick_length > 0:
                            tick_y1 = bar_y - self.config.tick_length if self.config.label_position == LabelPosition.TOP else bar_y + self.config.height
                            tick_y2 = bar_y if self.config.label_position == LabelPosition.TOP else bar_y + self.config.height + self.config.tick_length
                            draw.line([x_pos, tick_y1, x_pos, tick_y2], fill=self.config.border_color)

            # Título
            if title:
                title_y = bar_y + self.config.height + self.config.font_size + 10 if self.config.label_position == LabelPosition.BOTTOM else bar_y - self.config.font_size * 2 - 10
                draw.text(
                    (bar_x + self.config.width // 2, title_y),
                    title,
                    fill=self.config.label_color,
                    font=font,
                    anchor="mt" if self.config.label_position == LabelPosition.BOTTOM else "mb"
                )

        else:  # Vertical
            # Labels verticais
            x_offset = self.config.width + 5 if self.config.label_position == LabelPosition.RIGHT else -5

            # Min (bottom) e max (top)
            draw.text(
                (bar_x + x_offset, bar_y + self.config.height),
                min_label,
                fill=self.config.label_color,
                font=font,
                anchor="lm" if self.config.label_position == LabelPosition.RIGHT else "rm"
            )
            draw.text(
                (bar_x + x_offset, bar_y),
                max_label,
                fill=self.config.label_color,
                font=font,
                anchor="lm" if self.config.label_position == LabelPosition.RIGHT else "rm"
            )

            # Valores intermediários
            if intermediate_values:
                for value in intermediate_values:
                    if min_value < value < max_value:
                        y_pos = bar_y + self.config.height - int(
                            ((value - min_value) / (max_value - min_value)) * self.config.height)
                        label = custom_labels.get(value, f"{value}{unit}")
                        draw.text(
                            (bar_x + x_offset, y_pos),
                            label,
                            fill=self.config.label_color,
                            font=font,
                            anchor="lm" if self.config.label_position == LabelPosition.RIGHT else "rm"
                        )
                        # Tick mark
                        if self.config.tick_length > 0:
                            tick_x1 = bar_x + self.config.width if self.config.label_position == LabelPosition.RIGHT else bar_x - self.config.tick_length
                            tick_x2 = bar_x + self.config.width + self.config.tick_length if self.config.label_position == LabelPosition.RIGHT else bar_x
                            draw.line([tick_x1, y_pos, tick_x2, y_pos], fill=self.config.border_color)

    def to_base64(self, img: Image.Image, format: str = 'PNG') -> str:
        """
        Converte imagem PIL para base64.

        Args:
            img: Imagem PIL
            format: Formato da imagem (PNG, JPEG, etc.)

        Returns:
            String base64 com data URI
        """
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = f"image/{format.lower()}"

        return f"data:{mime_type};base64,{img_base64}"

    def to_bytes(self, img: Image.Image, format: str = 'PNG') -> bytes:
        """
        Converte imagem PIL para bytes.

        Args:
            img: Imagem PIL
            format: Formato da imagem

        Returns:
            Bytes da imagem
        """
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()

    def create_categorical_legend(
            self,
            categories: Dict[str, Union[Tuple[int, int, int], str]],
            title: str = "",
            box_size: int = 20,
            spacing: int = 5,
            columns: int = 1
    ) -> Image.Image:
        """
        Cria uma legenda categórica com caixas de cores e labels.

        Args:
            categories: Dicionário {label: cor}
            title: Título da legenda
            box_size: Tamanho das caixas de cor
            spacing: Espaçamento entre itens
            columns: Número de colunas

        Returns:
            Imagem da legenda
        """
        font = self._get_font()

        # Converter cores e calcular dimensões
        items = []
        max_text_width = 0

        # Create a temporary draw object to measure text
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        for label, color in categories.items():
            if isinstance(color, str):
                color = self.hex_to_rgb(color)

            # Calcular largura do texto
            bbox = temp_draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            max_text_width = max(max_text_width, text_width)

            items.append((label, color))

        # Calcular layout
        item_width = box_size + spacing + max_text_width
        item_height = max(box_size, self.config.font_size) + spacing

        rows = (len(items) + columns - 1) // columns

        # Dimensões totais
        width = columns * item_width + 2 * self.config.margin
        height = rows * item_height + 2 * self.config.margin

        if title:
            height += self.config.font_size + spacing

        # Criar imagem
        img = Image.new('RGBA', (width, height), self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Adicionar título
        y_offset = self.config.margin
        if title:
            title_font = self._get_font(int(self.config.font_size * 1.2))
            draw.text(
                (width // 2, y_offset),
                title,
                fill=self.config.label_color,
                font=title_font,
                anchor="mt"
            )
            y_offset += int(self.config.font_size * 1.2) + spacing

        # Desenhar itens
        for i, (label, color) in enumerate(items):
            row = i // columns
            col = i % columns

            x = self.config.margin + col * item_width
            y = y_offset + row * item_height

            # Caixa de cor
            draw.rectangle(
                [x, y, x + box_size - 1, y + box_size - 1],
                fill=color,
                outline=self.config.border_color,
                width=self.config.border_width
            )

            # Label
            text_y = y + box_size // 2
            draw.text(
                (x + box_size + spacing, text_y),
                label,
                fill=self.config.label_color,
                font=font,
                anchor="lm"
            )

        return img


# Funções auxiliares para uso rápido
def create_height_scalebar(
        width: int = 300,
        height: int = 50,
        orientation: str = "horizontal",
        show_labels: bool = True
) -> Tuple[Image.Image, str]:
    """
    Cria scale bar para banda height do Open Buildings.

    Returns:
        Tupla (imagem PIL, base64)
    """
    config = ScaleBarConfig(
        width=width,
        height=height,
        orientation=Orientation(orientation),
        show_labels=show_labels
    )

    generator = ScaleBarGenerator(config)

    colors = [
        "002873", "1e6caf", "39a7b4", "7ecf4c",
        "b4d96f", "ffe971", "ffb347", "ff7c39", "ff0000"
    ]

    img = generator.create_scale_bar(
        colors=colors,
        min_value=0,
        max_value=80,
        unit="m",
        title="Altura (metros)",
        intermediate_values=[20, 40, 60]
    )

    base64_str = generator.to_base64(img)

    return img, base64_str


def create_presence_scalebar(
        width: int = 300,
        height: int = 50,
        orientation: str = "horizontal",
        show_labels: bool = True
) -> Tuple[Image.Image, str]:
    """
    Cria scale bar para banda presence do Open Buildings.

    Returns:
        Tupla (imagem PIL, base64)
    """
    config = ScaleBarConfig(
        width=width,
        height=height,
        orientation=Orientation(orientation),
        show_labels=show_labels,
        continuous=False  # Cores discretas para presence
    )

    generator = ScaleBarGenerator(config)

    colors = ["000000", "2446c0", "2ca02c", "ffdd57"]

    img = generator.create_scale_bar(
        colors=colors,
        min_value=0,
        max_value=1,
        unit="",
        title="Presença de Edificação",
        custom_labels={0: "Ausente", 1: "Presente"}
    )

    base64_str = generator.to_base64(img)

    return img, base64_str