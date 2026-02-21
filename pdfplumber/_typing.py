from collections.abc import Iterable, Sequence
from typing import Any, Literal, Union

T_seq = Sequence
T_num = Union[int, float]
T_point = tuple[T_num, T_num]
T_bbox = tuple[T_num, T_num, T_num, T_num]
T_obj = dict[str, Any]
T_obj_list = list[T_obj]
T_obj_iter = Iterable[T_obj]
T_dir = Union[Literal["ltr"], Literal["rtl"], Literal["ttb"], Literal["btt"]]
