"""Process-local Cube reset RNG repair. No planner/state input changes.

The installed Cube.reset drops its seed before calling its parent. Its parent
also samples two stabilization commands from an action_space property that
creates a fresh, unseeded Box on every access. Dataset qpos/qvel restoration
does not restore the warm-start/control state left by those commands.
"""
import gymnasium as gym

def install_cube_adapter(env):
 original=type(env)
 class PairedCube(original):
  @property
  def action_space(self):
   if not hasattr(self,'_research_action_space'):
    self._research_action_space=original.action_space.fget(self)
   return self._research_action_space
  def reset(self,seed=None,options=None,*args,**kwargs):
   if seed is not None:
    gym.Env.reset(self,seed=seed)
    self.action_space.seed(seed)
   seed_method=self.variation_space.seed
   def propagated(value=None):return seed_method(seed if value is None else value)
   self.variation_space.seed=propagated
   try:return super().reset(seed=seed,options=options,*args,**kwargs)
   finally:self.variation_space.seed=seed_method
 env.__class__=PairedCube
 return env
