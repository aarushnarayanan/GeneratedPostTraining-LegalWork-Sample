# Attribution

## Documents

The files under `tasks/**/documents/` are contracts that companies filed publicly with the U.S.
Securities and Exchange Commission. Their text is reproduced, without changes, from:

> Dan Hendrycks, Collin Burns, Anya Chen, Spencer Ball.
> *CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review.* NeurIPS 2021.
> The Atticus Project. https://www.atticusprojectai.org/cuad
> Repository: https://github.com/TheAtticusProject/cuad (commit `67faa0e6023b04fcaae6cc09497ab00e5d63a2a2`, `data.zip`)

CUAD is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Rubric criteria whose `basis` begins with `cuad:` rely on CUAD's clause annotations. The wording of
those criteria is new, and the CUAD authors have not reviewed or endorsed it.

## Structure

The task layout, criterion fields and all-pass scoring follow the design of Harvey LAB
(https://github.com/harveyai/harvey-labs, MIT licence). No LAB code, tasks or documents are included.
