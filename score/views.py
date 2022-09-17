from urllib import request
from django.shortcuts import render
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import json
import numpy as np
from faker import Factory
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
import collections


# Create your views here.

colorPalette = [
    "#55efc4",
    "#81ecec",
    "#a29bfe",
    "#ffeaa7",
    "#fab1a0",
    "#ff7675",
    "#fd79a8",
]
colorPrimary, colorSuccess, colorDanger = "#79aec8", colorPalette[0], colorPalette[5]


def index(request):
    return render(request, "index.html")


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def proposl_info(request):
    return render(request, "praposal_info.html")


def dao(request):
    data = get_data()
    print(data)
    return render(request, "dao.html", {"name": "Compound Dao", "data": data})


def set_chart(request):
    if request.method == "POST":
        df = get_data()
        data = {
            "vote_data": get_graph_values(
                get_voting_data(df)[0],
                get_voting_data(df)[1],
                get_voting_data(df)[2],
                get_voting_data(df)[3],
                get_voting_data(df)[4],
            ),
            "voter_data": get_graph_values(
                get_voter_graph(df)[0],
                get_voter_graph(df)[1],
                get_voter_graph(df)[2],
                get_voter_graph(df)[3],
                get_voter_graph(df)[4],
            ),
            "praposals_data": get_graph_values(
                get_praposals_data(df)[0],
                get_praposals_data(df)[1],
                get_praposals_data(df)[2],
                get_praposals_data(df)[3],
                get_praposals_data(df)[4],
            ),
            "proposals": str(get_proposals(df)),
        }
        return JsonResponse(data, encoder=NpEncoder)


def get_voter_graph(df):
    df_VoteCast = df[df["name"] == "VoteCast"]
    for i in range(0, 4):
        name = df_VoteCast[i][1]["name"]
        df_VoteCast[name] = df_VoteCast[i].apply(lambda x: x["value"])
    df_final_VoteCast = df_VoteCast[
        [
            "block_signed_at",
            "block_height",
            "tx_hash",
            "voter",
            "proposalId",
            "support",
            "votes",
        ]
    ]
    df_final_VoteCast["votes"] = df_final_VoteCast["votes"].astype(float)
    df_final_VoteCast["votes"] = df_final_VoteCast["votes"] / 10**18
    df_final_VoteCast["proposalId"] = df_final_VoteCast["proposalId"].astype(int)

    count = pd.Series(df_final_VoteCast["voter"].value_counts()).to_dict()
    votes = pd.Series(df_final_VoteCast.groupby("voter").sum()["votes"]).to_dict()
    address = []
    votes_count = []
    voted_for_count = []

    for i in collections.OrderedDict(count):
        address.append(i)
        votes_count.append(votes[i])
        voted_for_count.append(count[i])

    return (
        address[0:10],
        votes_count[0:10],
        voted_for_count[0:10],
        "Total Vote",
        "Numbers of Praposals Voted For",
    )


def get_graph_values(lables, x1, x2, x1_label, x2_label):
    bg_color_true = []
    bg_color_false = []
    fake = Factory.create()
    for i in range(len(lables)):
        bg_color_true.append(colorPalette[2])
        bg_color_false.append(colorPalette[5])

    support_true_data = {
        "label": x1_label,
        "backgroundColor": bg_color_true,
        "borderColor": colorPrimary,
        "data": list(x1),
    }
    support_false_data = {
        "label": x2_label,
        "backgroundColor": bg_color_false,
        "borderColor": colorPrimary,
        "data": list(x2),
    }
    data = {
        "labels": list(lables),
        "datasets": [support_true_data, support_false_data],
    }
    return data


def get_praposals_data(df):
    df_ProposalCreated = df[df["name"] == "ProposalCreated"]
    for i in range(0, 9):
        name = df_ProposalCreated.reset_index()[i][1]["name"]
        df_ProposalCreated[name] = df_ProposalCreated[i].apply(lambda x: x["value"])
    df_final_ProposalCreated = df_ProposalCreated[
        ["block_signed_at", "block_height", "tx_hash", "id", "proposer", "description"]
    ]
    total_praposal_created = dict(df_ProposalCreated["proposer"].value_counts())
    df_ProposalExecuted = df[df["name"] == "ProposalExecuted"]
    for i in range(0, 1):
        name = df_ProposalExecuted.reset_index()[i][1]["name"]
        df_ProposalExecuted[name] = df_ProposalExecuted[i].apply(lambda x: x["value"])
    df_final_ProposalExecuted = df_ProposalExecuted[
        ["block_signed_at", "block_height", "tx_hash", "id"]
    ]
    df_final_ProposalExecuted["exicuted"] = True
    df_proposals = pd.merge(
        df_final_ProposalCreated,
        df_final_ProposalExecuted,
        on="id",
        how="outer",
        suffixes=("_restaurant_id", "_restaurant_review"),
    )
    praposal_exicuted = dict(
        df_proposals[df_proposals["exicuted"] == True]["proposer"].value_counts()
    )
    praposal_exicute_user = []
    praposers = []
    praposal_created_user = []
    for i in total_praposal_created:
        praposers.append(i)
        praposal_created_user.append(total_praposal_created[i])
        try:
            praposal_exicute_user.append(praposal_exicuted[i])
        except:
            praposal_exicute_user.append(0)
    return (
        praposers,
        praposal_created_user,
        praposal_exicute_user,
        "Praposal Created",
        "Praposal Exicuted",
    )


def get_data():
    items = []
    for i in range(1, 14544855, 1000000):
        url = (
            "https://api.covalenthq.com/v1/1/events/address/0xc0da01a04c3f3e0be433606045bb7017a7323e38/?page-size=1000000&starting-block="
            + str(i)
            + "&ending-block="
            + str(i + 1000000)
            + "&key=ckey_733562fd03494fdab22255ab185"
        )
        headers = {"Accept": "application/json"}
        data = requests.get(url, headers=headers)
        if len(data.json()["data"]["items"]) != 0:
            items.extend(data.json()["data"]["items"])

    df = pd.DataFrame(items)
    df1 = pd.concat(
        [df.drop(["decoded"], axis=1), df["decoded"].apply(pd.Series)], axis=1
    )
    df2 = pd.concat(
        [df1.drop(["params"], axis=1), df1["params"].apply(pd.Series)], axis=1
    )
    return df2


def get_voting_data(df):
    df_VoteCast = df[df["name"] == "VoteCast"]
    for i in range(0, 4):
        name = df_VoteCast[i][1]["name"]
        df_VoteCast[name] = df_VoteCast[i].apply(lambda x: x["value"])
    df_final_VoteCast = df_VoteCast[
        [
            "block_signed_at",
            "block_height",
            "tx_hash",
            "voter",
            "proposalId",
            "support",
            "votes",
        ]
    ]
    df_final_VoteCast["votes"] = df_final_VoteCast["votes"].astype(float)
    df_final_VoteCast["votes"] = df_final_VoteCast["votes"] / 10**18
    df_final_VoteCast["proposalId"] = df_final_VoteCast["proposalId"].astype(int)
    proposalId = list(set(df_final_VoteCast["proposalId"]))
    support_true = list(
        df_final_VoteCast[df_final_VoteCast["support"] == True]
        .groupby(["proposalId"])
        .sum()["votes"]
    )
    support_false = list(
        df_final_VoteCast[df_final_VoteCast["support"] == False]
        .groupby(["proposalId"])
        .sum()["votes"]
    )

    return (proposalId, support_true, support_false, "Support", "Againts")


def get_proposals(df):
    df_ProposalCreated = df[df["name"] == "ProposalCreated"]
    for i in range(0, 9):
        name = df_ProposalCreated.reset_index()[i][1]["name"]
        df_ProposalCreated[name] = df_ProposalCreated[i].apply(lambda x: x["value"])
    df_final_ProposalCreated = df_ProposalCreated[
        ["block_signed_at", "block_height", "tx_hash", "id", "proposer", "description"]
    ]
    return dict(df_final_ProposalCreated[["id", "proposer", "description"]])
