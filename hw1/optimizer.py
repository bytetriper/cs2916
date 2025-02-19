from typing import Callable, Iterable, Tuple

import torch
from torch.optim import Optimizer
class AdamW(Optimizer):
    def __init__(
            self,
            params: Iterable[torch.nn.parameter.Parameter],
            lr: float = 1e-3,
            betas: Tuple[float, float] = (0.9, 0.999),
            eps: float = 1e-6,
            weight_decay: float = 0.0,
            correct_bias: bool = True,
    ):
        if lr < 0.0:
            raise ValueError("Invalid learning rate: {} - should be >= 0.0".format(lr))
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[0]))
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[1]))
        if not 0.0 <= eps:
            raise ValueError("Invalid epsilon value: {} - should be >= 0.0".format(eps))
        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay, correct_bias=correct_bias)
        super().__init__(params, defaults)

    def step(self, closure: Callable = None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError("Adam does not support sparse gradients, please consider SparseAdam instead")
                grad = grad.float()
                # State should be stored in this dictionary
                state = self.state[p]
                # State initialization if necessary
                if len(state) == 0:
                    state["step"] = (
                        torch.tensor(0.0)
                    )
                    # Exponential moving average of gradient values
                    state["exp_avg"] = torch.zeros_like(
                        p, memory_format=torch.preserve_format,dtype=torch.float32
                    )
                    # Exponential moving average of squared gradient values
                    state["exp_avg_sq"] = torch.zeros_like(
                        p, memory_format=torch.preserve_format,dtype=torch.float32
                    )
                
                # Increment the step counter
                state["step"] += 1

                # Access hyperparameters from the `group` dictionary
                alpha = group["lr"]

                # Update first and second moments of the gradients
                state["exp_avg"].mul_(group["betas"][0]).add_(grad, alpha=1 - group["betas"][0])
                state["exp_avg_sq"].mul_(group["betas"][1]).addcmul_(grad, grad, value=1 - group["betas"][1])
                # Bias correction
                exp_avg = state["exp_avg"] / (1 - torch.pow(group["betas"][0], state["step"]))
                exp_avg_sq = state["exp_avg_sq"] / (1 - torch.pow(group["betas"][1], state["step"]))
                # Please note that we are using the "efficient version" given in
                # https://arxiv.org/abs/1412.6980

                # Update parameters
                p.data.addcdiv_(exp_avg, (exp_avg_sq.sqrt() + group["eps"]), value=-alpha)

                # Add weight decay after the main gradient-based updates.
                # Please note that the learning rate should be incorporated into this update.   
                if group["weight_decay"] != 0:
                    p.data.add_(p.data, alpha=-group["weight_decay"] * alpha)
        return loss