import argparse
import logging
import numpy as np
import Dumbledraw.styles as styles


import ROOT as root


root.PyROOT.IgnoreCommandLineOptions = True
root.gROOT.SetBatch(True)
root.gStyle.SetPaintTextFormat(".3f")

unc_color_map = {
        1: root.TColor(3001, 0.8, 0.8, 0.8, "tGrey", 0.75),
        2: root.TColor(3002, 1., 0., 0., "tRed", 0.35),  # 625
        4: root.TColor(3003, 0., 0., 1., "tBlue", 0.35),  # 866
}

transparent = root.TColor(3100, 1., 1., 1., "tWhite", 0.0)
blue = root.TColor(3200, 0.12156862745098039, 0.4666666666666667, 0.7058823529411765, "myBlue",  1.0)
orange = root.TColor(3201, 1.0, 0.4980392156862745, 0.054901960784313725, "myOrange", 1.0)
trans_blue = root.TColor(3205, 0.12156862745098039, 0.4666666666666667, 0.7058823529411765, "myBlue",  0.5)
trans_orange = root.TColor(3206, 1.0, 0.4980392156862745, 0.054901960784313725, "myOrange", 0.5)


def setup_logging(lev=logging.INFO):
    logging.basicConfig(level=lev)
    return


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--era", type=str,
                        help="Plot scale factor as well.")
    parser.add_argument("--embedding", action="store_true",
                        dest="emb")
    parser.add_argument("-w", "--working-point", default="Tight",
                        help="Tau ID working point starting with capital letter.")
    return parser.parse_args()


def _draw_wp_name(text, textsize=0.04, begin_left=None):
    ypos = 0.960 if "_{" in text else 0.955
    latex2 = root.TLatex()
    latex2.SetNDC()
    latex2.SetTextAngle(0)
    latex2.SetTextColor(root.kBlack)
    latex2.SetTextSize(textsize)
    if begin_left is None:
        begin_left = 0.145
    latex2.DrawLatex(begin_left, ypos, text)
    return


def create_pad(name, upper_bound, lower_bound):
    pad = root.TPad("p_" + name, "p_" + name, 0., 0., 1., 1.)
    drawspaceheight = 1.0 - pad.GetBottomMargin(
    ) - pad.GetTopMargin()
    lower_margin = pad.GetBottomMargin(
    ) + lower_bound * drawspaceheight
    upper_margin = pad.GetTopMargin() + (
        1 - upper_bound) * drawspaceheight
    pad.SetBottomMargin(lower_margin)
    pad.SetTopMargin(upper_margin)
    return pad


def plot_1d_with_ratio(names, inps, cols, args):
    # Create pad structure.
    canvas = root.TCanvas("c1", "c1", 800, 800)
    upper_pad = root.TPad("p_upper", "p_upper", 0., 0.3, 1., 1.)

    upper_pad.Draw()
    canvas.cd()
    ratio_pad = root.TPad("p_ratio", "p_ratio", 0., 0., 1., 0.35)
    ratio_pad.Draw()

    upper_pad.cd()
    upper_pad.SetLogx()
    upper_pad.SetGrid()
    ratio_pad.SetLogx()
    ratio_pad.SetGrid()

    scale_w_pad = (canvas.GetWw()*canvas.GetAbsWNDC())/(upper_pad.GetWw()*upper_pad.GetAbsWNDC())
    scale_h_pad = (canvas.GetWh()*canvas.GetAbsHNDC())/(upper_pad.GetWh()*upper_pad.GetAbsHNDC())
    scale_w_ratio = (canvas.GetWw()*canvas.GetAbsWNDC())/(ratio_pad.GetWw()*ratio_pad.GetAbsWNDC())
    scale_h_ratio = (canvas.GetWh()*canvas.GetAbsHNDC())/(ratio_pad.GetWh()*ratio_pad.GetAbsHNDC())
    upper_pad.SetTopMargin(upper_pad.GetTopMargin()*scale_h_pad)
    ratio_pad.SetBottomMargin(ratio_pad.GetBottomMargin()*scale_h_ratio)

    # Build empty dummy histogram to prepare plots.
    hDummy = root.TH1F("hDummy", "hDummy",
                       1, 18, 500)
    hDummy.SetAxisRange(0, 1.05, "Y")
    hDummy.SetXTitle("")
    hDummy.SetYTitle("L1 + HLT Efficiency")
    hDummy.GetXaxis().SetMoreLogLabels()
    hDummy.GetYaxis().SetRangeUser(0., 1.1)
    hDummy.GetXaxis().SetLabelOffset(999)

    hDummy.GetYaxis().SetTitleSize(hDummy.GetYaxis().GetTitleSize()*scale_h_pad)
    hDummy.GetYaxis().SetLabelSize(hDummy.GetYaxis().GetLabelSize()*scale_h_pad)
    hDummy.GetYaxis().SetTitleOffset(hDummy.GetYaxis().GetTitleOffset()/scale_h_pad)
    hDummy.GetXaxis().SetLabelSize()
    hDummy.Draw()

    # Create filled histogram to hatch area.
    hHatch = root.TH1F("hHatch", "hHatch",
                       1, 18, hatch_map[args.year][args.trg])
    hHatch.SetBinContent(1, 1.1)
    hHatch.SetFillColor(21)
    hHatch.SetFillStyle(3444)
    hHatch.Draw("same l0")

    graphs, f1s = [], []
    if args.include_uncerts:
        uncs = []
    for inp, col, name in zip(inps, cols, names):
        graph = inp.Get(name)
        logging.info("Querying graph %s", name)
        tf1 = inp.Get(name.replace("graph", "fit"))
        if (not isinstance(tf1, root.TF1)
                and not isinstance(graph, root.TGraphAsymmErrors)):
            logging.fatal("Function %s not found in file %s",
                          name, inp.GetName())
            raise Exception
        graphs.append(graph)
        f1s.append(tf1)
        graphs[-1].SetLineColor(col)
        graphs[-1].SetMarkerColor(col)
        f1s[-1].SetLineColor(col)
        if args.include_uncerts:
            unc = inp.Get(name.replace("graph", "errorBand"))
            if not isinstance(unc, root.TH1F):
                logging.fatal("Histogram %s not found in file %s",
                              name, inp.GetName())
                raise Exception
            unc.SetLineColor(transparent.GetNumber())
            unc.SetMarkerColor(transparent.GetNumber())
            # unc.SetFillColor(unc_color_map[col].GetNumber())
            uncs.append(unc)
        if args.include_uncerts:
            uncs[-1].Draw("same e3")
        graphs[-1].Draw("same ep")
        f1s[-1].Draw("same l")
    leg = root.TLegend(0.75, 0.4, 0.95, 0.55)
    for graph, inp, legname in zip(graphs, inps, args.legend):
        leg.AddEntry(graph, legname, "lep")
    leg.Draw()
    if args.year == 2016:
        styles.DrawTitle(upper_pad, "35.9 fb^{-1} (2016, 13 TeV)", 3)
    elif args.year == 2017:
        styles.DrawTitle(upper_pad, "41.5 fb^{-1} (2017, 13 TeV)", 3)
    elif args.year == 2018:
        styles.DrawTitle(upper_pad, "59.7 fb^{-1} (2018, 13 TeV)", 3)
    else:
        logging.fatal("Year %s not known.", args.year)
        raise Exception
    _draw_wp_name("{}, {}, {}".format(args.trg, args.wp, args.sample),
                  begin_left=0.16)

    # Set up ratio plot.
    ratio_pad.cd()
    if args.year == 2016:
        y_range = [0.75, 1.55]
    else:
        y_range = [0.45, 1.15]
    # Build empty dummy histogram to prepare plots.
    hRatioDummy = root.TH1F("hRatioDummy", "hRatioDummy",
                       1, 18, 500)
    hRatioDummy.SetAxisRange(*(y_range + ["Y"]))
    hRatioDummy.SetXTitle("Hadronic Tau p_{T} / GeV")
    hRatioDummy.SetYTitle("SF")
    hRatioDummy.GetXaxis().SetMoreLogLabels()
    hRatioDummy.GetYaxis().SetRangeUser(*y_range)
    hRatioDummy.GetXaxis().SetLabelSize(hRatioDummy.GetXaxis().GetLabelSize()*scale_h_ratio)
    hRatioDummy.GetXaxis().SetTitleSize(hRatioDummy.GetXaxis().GetTitleSize()*scale_h_ratio)
    hRatioDummy.GetXaxis().SetTitleOffset(hRatioDummy.GetXaxis().GetTitleOffset()/scale_w_ratio)
    hRatioDummy.GetYaxis().SetLabelSize(hRatioDummy.GetYaxis().GetLabelSize()*scale_h_ratio)
    hRatioDummy.GetYaxis().SetTitleSize(hRatioDummy.GetYaxis().GetTitleSize()*scale_h_ratio)
    hRatioDummy.GetYaxis().SetNdivisions(305)
    hRatioDummy.GetYaxis().SetTitleOffset(hRatioDummy.GetYaxis().GetTitleOffset()/scale_h_ratio)
    hRatioDummy.Draw()

    # Create filled histogram to hatch area.
    hRatioHatch = root.TH1F("hRatioHatch", "hRatioHatch",
                       1, 18, hatch_map[args.year][args.trg])
    hRatioHatch.SetBinContent(1, y_range[1])
    hRatioHatch.SetFillColor(21)
    hRatioHatch.SetFillStyle(3444)
    hRatioHatch.Draw("same l0")

    f_ratio = root.TF1("ratio", names[0].replace("graph", "fit")+"/"+names[1].replace("graph", "fit"), 18, 500)
    #for ipar in range(f_ratio.GetNpar()):
    par_vals = [f1s[0].GetParameter(i) for i in range(f1s[0].GetNpar())] + [f1s[1].GetParameter(i) for i in range(f1s[1].GetNpar())]
    for ipar in range(f1s[0].GetNpar()):
        print ipar, f1s[0].GetParName(ipar), f1s[0].GetParameter(ipar)
    for ipar, parval in enumerate(par_vals):
        print ipar, parval
        print f_ratio.GetParName(ipar)
        f_ratio.SetParameter(ipar, parval)
    f_ratio.SetLineColor(4)
    f_ratio.SetLineWidth(2)
    f_ratio.Draw("same l")
    if args.include_uncerts:
        unc = inp.Get(names[0].replace("graph", "errorBand"))
        if not isinstance(unc, root.TH1F):
            logging.fatal("Histogram %s not found in file %s",
                          name, inp.GetName())
            raise Exception
        unc.SetLineColor(transparent.GetNumber())
        unc.SetMarkerColor(transparent.GetNumber())
        unc.SetFillColor(unc_color_map[col].GetNumber())
        # Loop over histogram and set value and error.
        for ibin in range(1, unc.GetNbinsX() + 1):
            bin_cen = unc.GetBinCenter(ibin)
            unc.SetBinContent(ibin, f_ratio.Eval(bin_cen))
            data_unc = uncs[0].GetBinErrorLow(ibin)/uncs[0].GetBinContent(ibin)
            mod_unc = uncs[1].GetBinErrorLow(ibin)/uncs[1].GetBinContent(ibin)
            sigma = np.sqrt(data_unc**2 + mod_unc**2)
            unc.SetBinError(ibin, f_ratio.Eval(bin_cen)*sigma)
        unc.Draw("same e3")
    canvas.Update()
    # canvas.Print("plots/"+args.title+".png", "png")
    canvas.Print("plots/"+args.title+"_ratio.pdf", "pdf")
    return


def plot_1d(names, inps, cols, args=None, legend=None, wp="Tight"):
    canvas = root.TCanvas()
    canvas.SetLogx()
    # canvas.SetGrid()
    hDummy = root.TH1F("hDummy", "hDummy",
                       1, 30, 1000)
    hDummy.SetAxisRange(0.6, 1.15, "Y")
    hDummy.SetXTitle("Hadronic Tau p_{T} / GeV")
    hDummy.SetYTitle("Tau ID SF")
    hDummy.GetXaxis().SetMoreLogLabels()
    hDummy.GetYaxis().SetRangeUser(0.6, 1.15)
    hDummy.Draw()

    f1s = []
    uncs_up = []
    uncs_down = []
    for name, inp, col in zip(names, inps, cols):
        logging.info("Querying graph %s", name)
        tf1 = inp.Get(name)
        if (not isinstance(tf1, root.TF1)):
            logging.fatal("Function %s not found in file %s",
                          name, inp.GetName())
            raise Exception
        f1s.append(tf1)
        f1s[-1].SetLineColor(col)
        f1s[-1].SetLineWidth(2)
        unc_up = inp.Get(name.replace("cent", "up"))
        unc_down = inp.Get(name.replace("cent", "down"))
        if (not isinstance(unc_up, root.TF1) or
            not isinstance(unc_down, root.TF1)):
            logging.fatal("Uncertainty for %s not found in file %s",
                          name, inp.GetName())
            raise Exception
        unc_up.SetLineColor(col+5)
        unc_up.SetLineWidth(2)
        unc_up.SetLineStyle(2)
        unc_up.SetMarkerColor(col+5)
        # unc_up.SetFillColor(unc_color_map[col].GetNumber())
        uncs_up.append(unc_up)
        uncs_up[-1].Draw("same l")
        unc_down.SetLineColor(col+5)
        unc_down.SetLineWidth(2)
        unc_down.SetLineStyle(2)
        unc_down.SetMarkerColor(col+5)
        # unc_down.SetFillColor(unc_color_map[col].GetNumber())
        uncs_down.append(unc_down)
        uncs_down[-1].Draw("same l")
        f1s[-1].Draw("same l")
    leg = root.TLegend(0.25, 0.15, 0.95, 0.3)
    for f1, legname in zip(f1s, legend):
        leg.AddEntry(f1, legname, "l")
    leg.Draw()
    if args.era == "2016":
        styles.DrawTitle(canvas, "35.9 fb^{-1} (2016, 13 TeV)", 3)
    elif args.era == "2017":
        styles.DrawTitle(canvas, "41.5 fb^{-1} (2017, 13 TeV)", 3)
    elif args.era == "2018":
        styles.DrawTitle(canvas, "59.7 fb^{-1} (2018, 13 TeV)", 3)
    else:
        logging.fatal("Year %s not known.", args.era)
        raise Exception
    _draw_wp_name("{} DeepTau vs jets, {}".format(wp, "EMB" if args.emb else "MC"),
                  begin_left=0.16, textsize=0.035)
    canvas.Update()
    # canvas.Print("plots/"+args.title+".png", "png")
    canvas.Print("plots/tau_id_comparison_vs_electron_wp_{}{}.pdf".format(args.era, "_EMB" if args.emb else ""), "pdf")
    canvas.Print("plots/tau_id_comparison_vs_electron_wp_{}{}.png".format(args.era, "_EMB" if args.emb else ""), "png")
    return


def main(args):
    styles.SetStyle("ModTDR")
    root.gStyle.SetOptStat(0)
    root.gStyle.SetOptFit(root.kFALSE)
    root.gStyle.SetHatchesLineWidth(1)
    root.gStyle.SetHatchesSpacing(1.)
    era_dict = {
            "2016": "2016Legacy",
            "2017": "2017ReReco",
            "2018": "2018ReReco",
            }
    input_name = "data/TauID_SF_pt_DeepTau2017v2p1VSjet_{}{}.root".format(era_dict[args.era], "_EMB" if args.emb else "")
    inp_files = [root.TFile(input_name, "read")]
    inp_files.append(root.TFile(input_name.replace(".root", "_tight_antie.root") if not args.emb
                                else input_name.replace("_EMB", "_tight_antie_EMB"), "read"))
    print inp_files
    hist_names = ["{}_cent".format(args.working_point) for i in range(2)]
    print hist_names
    logging.info("Plotting fit functions and histograms from file:")
    for inp in inp_files:
        logging.info("%s", inp.GetName())
    # fname = "{}_tightMVAv2_{}_{}_fit".format(trg, dm, ty)
    legend = ["Very loose DeepTau vs electrons", "Tight DeepTau vs electrons"]
    color_list = [3200, 3201]
    plot_1d(hist_names, inp_files, color_list, args, legend=legend, wp=args.working_point)
    return


if __name__ == "__main__":
    setup_logging(logging.INFO)
    args = parse_arguments()
    main(args)
