# Created by hborcher at 2/2/2018
Feature: Build package objects
  # You should easily be able to build a new package object using the package factory

  Scenario: Capture One session containing 2 objects
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    Then resulting packages should be 2
    And the first Capture One object should contain everything from the first group
    And the second Capture One object should contain everything from the second group

  Scenario: Hathi TIFF package containing 2 objects
    Given We have hathi tiff package containing a folder made up of 2 objects
    When we create a HathiTiff object factory and use it to identify packages at the root folder
    Then resulting packages should be 2
    And the first Hathi TIFF object should contain everything from the first group
    And the second Hathi TIFF object should contain everything from the second group

  Scenario: Capture One session containing 2 objects and want to transform them into a HathiTrust Tiff package
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    And we transform all the packages found into Hathi tiff packages
    Then the newly transformed package should contain the same files but in the format for Hathi Trust