import gradio as gr
import sqlite3
import re
import json
from config import WHITELIST, rdb

ServerList = WHITELIST["ServerList"]
UserList = WHITELIST["UserList"]
ChannelList={}
for _ in ServerList:
    ChannelList.update(ServerList[_]["Channels"])
#ChannelList.update(UserList)

starting_list = []
class conf():
    def __init__(self):
        self.most_recent = "N/A"
        self.least_recent = "N/A"
        self.context = "N/A"
        self.history = "N/A"
        self.reply = "N/A"
        self.remaining = 0
        self.starting_list = []
        self.final_list = []
        self.indexes = [("<7>","<9>"), ("<6>","<8>"), ("<5>","<7>"), ("<4>","<6>"), ("<3>", "<5>"), ("<2>","<4>"), ("<1>","<3>"), ("<0>","<2>")]
    def cycle(self, string):
        self.least_recent = self.most_recent
        self.most_recent = string


cfg = conf()

def load_data():
    return cfg.starting_list.pop(0)

def save_instance(context, history, output):
    cfg.context = context.strip()
    cfg.history = history.strip()
    cfg.reply = output.strip()
    data = {
        "context": cfg.context,
        "history": cfg.history,
        "output": cfg.reply,
    }
    cfg.final_list.append(data)
    data_str = f"{cfg.context}\n{cfg.history}\n{cfg.reply}"
    cfg.cycle(data_str)
    return

def export_json():
    final = json.dumps(final, ensure_ascii=False, indent=4)
    with open("./cleaned_sqldb.json", "x", encoding='utf-8') as outfile:
        outfile.write(final)
    quit()

def save_continue(context, history, reply):
    save_instance(context, history, reply)
    cfg.history = f"{cfg.history} <0>[Bot]: {cfg.reply}"
    for _ in cfg.indexes: #Shifts indexes up by 2
        cfg.history = cfg.history.replace(_[0], _[1])
    cfg.history = f"{cfg.history} <1>Elle: "
    return cfg.history, "", cfg.remaining, cfg.least_recent, cfg.most_recent

def save_next(context, history, reply):
    save_instance(context, history, reply)
    new_context, new_history, new_reply = load_data()
    cfg.remaining -= 1
    return new_context, new_history, new_reply, cfg.remaining, cfg.least_recent, cfg.most_recent

def export_quit():
    export_json()

def reject():
    new_context, new_history, new_reply = load_data()
    cfg.remaining -= 1
    return new_context, new_history, new_reply, cfg.remaining, cfg.least_recent, cfg.most_recent

for _ in ChannelList:
    try:
        message_list = rdb.get_messages(_, ["context", "history", "reply"])
        for tuple in message_list:
            cfg.starting_list.append(tuple)
    except:
        channel_name = {ChannelList[_]["Name"]}
        print(f"{channel_name} not found")

cfg.remaining = len(cfg.starting_list)
cfg.context, cfg.history, cfg.reply = load_data()

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            context_box = gr.components.Textbox(lines=2, value=cfg.context, interactive=True, label="Context")
            history_box = gr.components.Textbox(lines=5, value=cfg.history, interactive=True, label="History")
            reply_box = gr.components.Textbox(lines=2, value=cfg.reply, interactive=True, label="Reply")
        
        with gr.Column():
            progress_box = gr.components.Textbox(lines=1, interactive=False, value=cfg.remaining, label="Sequences remaining")
            less_recent_box = gr.components.Textbox(lines=5, placeholder=cfg.least_recent, label="Less recent")
            more_recent_box = gr.components.Textbox(lines=5, placeholder=cfg.least_recent, label="Less recent")

    with gr.Row():
        export_btn = gr.Button("Export & Quit")
        export_btn.click(fn=export_quit)

        reject_btn = gr.Button(fn=reject, label="Reject")
        reject_btn.click(fn=reject, outputs = [context_box, history_box, reply_box, progress_box, less_recent_box, more_recent_box])
        
        continue_btn = gr.Button("Save & Continue")
        continue_btn.click(fn=save_continue, inputs=[context_box, history_box, reply_box], outputs = [history_box, reply_box, progress_box, less_recent_box, more_recent_box])
        
        next_btn = gr.Button("Save & Next")
        next_btn.click(fn=save_next, inputs=[context_box, history_box, reply_box], outputs = [context_box, history_box, reply_box, progress_box, less_recent_box, more_recent_box])

if __name__ == "__main__":
    demo.launch()
