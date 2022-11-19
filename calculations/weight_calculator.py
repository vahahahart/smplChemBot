from os import path
import re
from json import load
from decimal import Decimal as Dc


p = path.join(path.dirname(path.abspath(__file__)), r'mol_weights.json')

with open(p) as f:
    weights_dict = load(f)


def formula_to_weight(formula: str, global_mult=Dc(1), full_weight=Dc(0)):
    split_formula = re.split(r'\s*\*\s*', formula)
    for compound in split_formula:
        mult = global_mult
        match_list = re.findall(r'\d+|\(.*\)\d*|[A-Z][a-z\d]*', compound)

        for frag in match_list:
            if re.fullmatch(r'^\d+', frag):
                mult = mult * Dc(frag)

            elif re.fullmatch(r'[A-z]+\b', frag):
                el_weight = weights_dict[frag]
                full_weight += Dc(el_weight) * mult

            else:
                complex_frag = re.fullmatch(r'\((.*)\)(\d+)$|([A-z]+)(\d+)$', frag).groups()
                complex_frag = list(filter(lambda x: bool(x), complex_frag))
                full_weight += formula_to_weight(complex_frag[0], mult * Dc(complex_frag[1]))

    if full_weight == Dc(0):
        raise KeyError
    return full_weight
