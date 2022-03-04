#This script takes the output root file from fliPlotter.py and add a flip
#It should be run inside a CMSSW environment (11_0_0+ works)
#It uses a gaussian fit with CMSSShape for background
#Requires RooCMSShape.cc and RooCMSShape.h in the location

import ROOT
ROOT.gSystem.Load('')
ROOT.gInterpreter.Declare('#include "RooCMSShape.cc"')


def rf201_composite():

    inFile  = ROOT.TFile.Open("Drell_Yan_output.root", "READ")
    hOS     = inFile.Get("OS_invmass")

    Z_mass  = ROOT.RooRealVar("Z_mass","Z mass", 60, 120, "GeV")
    hOS     = ROOT.RooDataHist("hOS", "hOS", ROOT.RooArgList(Z_mass), ROOT.RooFit.Import(hOS))

    #Parameters for gaus fit ("name", "name", initial_value, lower_limit, upper_limit)
    mean    = ROOT.RooRealVar("mean", "mean of gaussians", 91.0, 90.0, 100.0)
    sigma1  = ROOT.RooRealVar("sigma1", "sigma1", 1.0, 0.1, 10.0)

    gaus1   = ROOT.RooGaussian("gaus1", "gaussian1", Z_mass, mean, sigma1)

    #Parameters for CMSShape fit ("name", "name", initial_value, lower_limit, upper_limit)  
    al      = ROOT.RooRealVar("al", "al", 79.0, 70.0, 100.0)
    beta    = ROOT.RooRealVar("beta", "beta", 0.1, 0.0, 10.0)
    #This one (lambda) is the one I think still needs adjusting. The value is the only one not displayed in the ttH plots
    #Small adjustments of this can cause the integral not to coverge causing the script to go into infinite loop
    lambda0 = ROOT.RooRealVar("lambda", "slope", 90.0, 60.0, 120.0)
    gamma   = ROOT.RooRealVar("gamma", "gamma", 0.2, 0.0, 2.0)
    bkg     = ROOT.RooCMSShape("bkg", "CMSModel", Z_mass, al, beta, gamma, lambda0)

    nsig    = ROOT.RooRealVar("nsig","#signal events", 100000, 1000, 10000000)
    nbkg    = ROOT.RooRealVar("nbkg", "nbkg", 100000, 1000, 10000000)
    
    model   = ROOT.RooAddPdf("model", "conv+bkg", ROOT.RooArgList(gaus1, bkg), ROOT.RooArgList(nsig, nbkg))

    #model.chi2FitTo(hOS)
    model.fitTo(hOS, ROOT.RooFit.SumW2Error(True), ROOT.RooFit.Minos(True), ROOT.RooFit.Range(60, 120))

    xframe = Z_mass.frame(ROOT.RooFit.Title("Test Gaus fit"))
    hOS.plotOn(xframe)
    model.plotOn(xframe)

    model.Print("t")

    c = ROOT.TCanvas("output", "output", 600, 600)
    ROOT.gPad.SetLeftMargin(0.15)
    xframe.GetYaxis().SetTitleOffset(1.4)
    xframe.Draw()

    c.SaveAs("Drell_Yan_output.png")
    print("Chi2=",xframe.chiSquare())

if __name__ == "__main__":
    rf201_composite()
