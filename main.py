import discord
import os
import io
from datetime import datetime as dt
import matplotlib.pyplot as plt
from ode_solver import System_of_eq
from quantum_builder import Quantum_Circuit


from qiskit import *
import numpy as np


class Context():
    def __init__(self):
        self.nld_flag = False
        self.continue_flag = False
        self.eqn_flag = True
        self.solve_flag = False
        self.cwq_flag = False
        self.q_state_flag = False


def parse_mgs(message):
    msg = message.content
    if msg.lower() == 'q':
        context.continue_flag = False
        context.nld_flag = False
        context.cwq_flag = False
        eqn_of_motion.restore_default()
        quantum_cord.restore_default()


def get_ics(msg):
    vec = msg.split(",")
    tspan = (0,float(vec.pop()))
    iCs = [float(i) for i in vec]
    return tspan, iCs


async def send_figure(fig, data_stream, message, box_name = ""):
    fig.savefig(data_stream, format='png', bbox_inches="tight", dpi = 80)
    plt.close()
    data_stream.seek(0)
    chart = discord.File(data_stream,filename="solution.png")
    embed = discord.Embed(title=box_name, description="", color=0x00ff00)
    embed.set_image( url="attachment://solution.png" )
    await message.channel.send(embed=embed, file=chart)


client = discord.Client()
context = Context()
eqn_of_motion = System_of_eq('NLD')
quantum_cord = Quantum_Circuit()


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    global client, context
    print(message.content.lower())
    parse_mgs(message)

    if message.author == client.user:
        return

    if message.content.lower().startswith("hi"):
        await message.channel.send("Hi, wellcome back!")
        return

    if message.content.lower() == 'clc':
        with open('test.txt') as f:
            data = f.read()
        await message.channel.send(data)
        return

    if message.content.startswith('$nld') or context.nld_flag:
        if not context.continue_flag:
            context.nld_flag = True
            context.continue_flag = True
            context.eqn_flag = True
            context.solve_flag = False
            await message.channel.send("Switched to nld mode")
            await message.channel.send("You can now enter the equations of motion, or 'q' to exit")
            return
        elif context.continue_flag:
            if message.content.lower() == 'reset':
                context.nld_flag = True
                context.continue_flag = True
                context.eqn_flag = True
                context.solve_flag = False
                eqn_of_motion.restore_default()
                await message.channel.send("You can now enter new equations of motion, or 'q' to exit")
                return
            elif context.solve_flag:
                tspan, iCs = get_ics(message.content)
                await message.channel.send("Integrating the differentials")
                eqn_of_motion.solve_ivp(tspan,iCs, 5000)
                fig, data_stream = await eqn_of_motion.plot_last(message)
                await send_figure(fig, data_stream, message)
                await message.channel.send("Enter solve to change initial conditions for current model.")
                await message.channel.send("Enter 'reset' to change the equations of motion, 'q' to exit")
                context.solve_flag = False
                return
            elif message.content.lower() == "solve":
                states = eqn_of_motion.states
                await message.channel.send("Please enter initial conditions for {0} and time span separated by comma".format(states))
                context.solve_flag = True
                context.eqn_flag = False
                return
            elif context.eqn_flag:
                eqn = message.content
                eqn = eqn.split('=')
                eqn[0] = eqn[0].lower().strip('d')
                eqn_of_motion.add_equation(eqn[1], eqn[0])
                await message.channel.send("equation for state '{0}' added".format(eqn[0]))
                await message.channel.send("Add more, or sove added states? [solve]")
                return
            else:
                context.nld_flag = False
                return

    if message.content.lower().startswith("$cwq") or context.cwq_flag:
        if not context.continue_flag:
            context.cwq_flag = True
            context.continue_flag = True
            context.q_state_flag = True
            await message.channel.send("Switched to Quantum mode")
            await message.channel.send("You can now enter Quantum gates to add to the circuit, or 'q' to exit")
            await message.channel.send("Please enter how many quantum bits you want to play with?")

        elif context.cwq_flag and context.continue_flag:
            print("continuing in q realm")

            if context.q_state_flag and quantum_cord.num_qbits == None:
                print("trying to set num qbits")
                try:
                    print(message.content)
                    num_qbits = int(message.content)
                    quantum_cord.init_ckt(num_qbits,num_qbits)
                    await message.channel.send("Nice, now you can add gates to your {0} qbits".format(num_qbits))
                    await message.channel.send("Remember to add the address after gate name separated by comma")

                except:
                    num_qbits = None
                    await message.channel.send("Please enter how many quantum bits you want to play with?")

            elif message.content.lower().startswith("add"):
                print("trying to set add gates")
                l = message.content.lower().strip("add ").split(" ")
                gate = l[0]
                address = l[1].split(",")
                if len(address)==1:
                    print("Adding 1 gate to ckt")
                    await quantum_cord.add_gate(gate,int(address[0]),0,message)
                elif len(address)>1:
                    print("Adding {0} gates to ckt".format(len(address)))
                    al = [int(i) for i in address]
                    await quantum_cord.add_gate(gate,*al,message)

            elif message.content.lower() == "show circuit":
                print("trying to set add gates")
                fig, op = quantum_cord.open_ckt()
                await send_figure(fig, op, message, "Your Quantum Circuit")

            elif message.content.lower() == "measure":
                quantum_cord.init_measure_block()
                fig, op = quantum_cord.open_ckt()
                await send_figure(fig, op, message, "Your Quantum Circuit")
                fig, op = quantum_cord.qsphere('classic')
                await send_figure(fig, op, message, "Q sphere after measurement")
                fig, op = quantum_cord.multi_vector('classic')
                await send_figure(fig, op, message, "Bloch sphere after measurement")

            elif message.content.lower() == "show quantum state":
                fig, op = quantum_cord.open_ckt()
                await send_figure(fig, op, message, "Your Quantum Circuit")
                fig, op = quantum_cord.qsphere('before_classic')
                await send_figure(fig, op, message, "Q sphere before measurement")
                fig, op = quantum_cord.multi_vector('before_classic')
                await send_figure(fig, op, message, "Bloch sphere before measurement")

        return



client.run(os.getenv("CHATLAB"))
