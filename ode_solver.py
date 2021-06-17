import io
import sympy
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from config import color_pallete as cp
from config import fontsize

class System_of_eq():
  def __init__(self,name='dydt'):
    self.name = name
    self.eqn_list = []
    self.states = []
    self._atoms = []
    self.last_history = None

  def restore_default(self):
    print('erasing last state')
    self.eqn_list = []
    self.states = []
    self._atoms = []
    self.last_history = None

  def add_equation(self,eqn,state):
    self.eqn_list.append(sympy.sympify(str(eqn)))
    self.states.append(state)
    self._set_atoms()
    state_set = set(self.states)
    atom_set = set([str(i) for i in self._atoms])
    limbo_states = list(state_set.symmetric_difference(atom_set))
    if limbo_states:
      print('Fowwing states are equationless')
      print(limbo_states)

  def _get_atoms(self):
    num_eqn = len(self.eqn_list)
    atom_list = []
    for i in range(num_eqn):
      atom_list += self.eqn_list[i].atoms(sympy.Symbol)
    atom_set = set(atom_list)
    return list(atom_set)

  def _set_atoms(self):
    self._atoms = self._get_atoms()

  def _get_subs(self,time,cordinates):
    subs_dict = {}
    subs_dict['t'] = time
    for i,v in enumerate(self.states):
      subs_dict[v] = cordinates[i]
    return subs_dict

  def evaluate_at(self,time,cordinates):
    assert len(self.states) == len(cordinates)
    subs_dict = self._get_subs(time,cordinates)
    return np.asarray([self.eqn_list[i].subs(subs_dict) for i in range(len(self.eqn_list))])

  def integrate_rk4(self,timespan,iCs):
    t = np.arange(timespan[0],timespan[1],timespan[2]) if len(timespan) == 3 else np.arange(timespan[0],timespan[1],1)
    assert len(self.states) == len(iCs)

    xi = np.zeros((len(t),len(iCs)))
    x1 = self.evaluate_at(t[0],iCs)
    for i in range(len(t)-1):
      ti = t[i]
      tip1 = t[i+1]
      ht = tip1 - ti
      x2 = self.evaluate_at(ti,x1)
      x3 = self.evaluate_at(ti+ht/2.0, x1 + (ht/2.0)*x2)
      x4 = self.evaluate_at(ti+ht/2.0, x1 + (ht/2.0)*x3 )
      x5 = self.evaluate_at(ti+ht, x1 + (ht)*x4)

      x6 = x1 + (ht/6.0)*(x2 + 2.0*x3 + 2.0*x4 + x5)
      x1 = x6
      xi[i] = x6

    self.last_history = xi
    return xi

  def solve_ivp(self,tspan,iCs,nmax=10000):
    soln = solve_ivp(self.evaluate_at, tspan, iCs, dense_output=True)
    t = np.linspace(tspan[0], tspan[1], nmax)
    data = soln.sol(t)
    self.last_history = data
    return data

  async def plot_last(self, message):
    data = self.last_history
    states = self.states
    print(len(states))
    await message.channel.send('Creating the plot...')

    fig = plt.figure(figsize=(10, 8), dpi=126)
    if len(data) > 2:
      ax = fig.add_subplot(1, 1, 1, projection='3d')
    else:
      ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    cmap = plt.cm.winter
    s = 10
    n= len(data[0])
    cmap = plt.cm.Spectral
    for i in range(0,n-s,s):
      datafrac = [j[i:i+s+1] for j in data[0:3]]
      ax.plot(*datafrac, color=cmap(i/n), alpha=0.6)
    # ax.set_axis_off()
    await message.channel.send('Setting the palette...')
    fig, ax = self.set_plot_color(fig, ax)
    await message.channel.send('Beaming the solution to you...')

    output = io.BytesIO()
    return fig, output

  def set_plot_color(self, fig, ax, show_legend=False):
    label_list = self.states
    title = 'Evolution of the state'
    if show_legend:
      ax.legend(fontsize=fontsize,labelcolor=cp['legend'],facecolor = cp['face'],edgecolor=cp['edge'])
    fig.set_facecolor(cp['face'])
    ax.set_facecolor(cp['face'])

    ax.set_xlabel(label_list[0])
    ax.set_ylabel(label_list[1])

    ax.spines["bottom"].set_color(cp['spine'])
    ax.spines["top"].set_color(cp['spine'])
    ax.spines["left"].set_color(cp['spine'])
    ax.spines["right"].set_color(cp['spine'])

    ax.yaxis.label.set_color(cp['label'])
    ax.xaxis.label.set_color(cp['label'])

    ax.yaxis.label.set_fontsize(fontsize * 1.25)
    ax.xaxis.label.set_fontsize(fontsize * 1.25)

    ax.tick_params(axis='x', colors=cp['tick'], labelsize= fontsize*0.75, size=5)
    ax.tick_params(axis='y', colors=cp['tick'], labelsize= fontsize*0.75, size=5)

    ax.set_title(title, fontsize=fontsize * 1.5, color = cp['title'], fontfamily = 'sans-serif')
    if len(label_list)>2:

      ax.set_zlabel(label_list[2])

      ax.zaxis.label.set_color(cp['label'])

      ax.zaxis.label.set_fontsize(fontsize)

      ax.tick_params(axis='z', colors=cp['tick'], labelsize= fontsize*0.75, size=5)

      ax.xaxis.pane.fill = False
      ax.xaxis.pane.set_edgecolor(cp['face'])
      ax.yaxis.pane.fill = False
      ax.yaxis.pane.set_edgecolor(cp['face'])
      ax.zaxis.pane.fill = False
      ax.zaxis.pane.set_edgecolor(cp['face'])
      ax.grid(False)

      ax.w_zaxis.line.set_color('w')
      ax.w_xaxis.line.set_color('w')
      ax.w_yaxis.line.set_color('w')

    return fig, ax
